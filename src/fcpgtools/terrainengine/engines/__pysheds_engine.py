import xarray as xr
import numpy as np
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster
from pysheds.view import ViewFinder
from pathlib import Path
from typing import Union, Optional
import fcpgtools.tools as tools
import fcpgtools.utilities as utilities
import fcpgtools.custom_types as custom_types
from fcpgtools.custom_types import Raster, PyShedsInputDict, PourPointValuesDict

engine_name = 'pysheds'
def initialize():
    return PyShedsEngine()

class PyShedsEngine:

    d8_format = 'esri'

    function_kwargs = {
        'accumulate_flow': custom_types.PyShedsFACkwargsDict.__annotations__,
        'accumulate_parameter': custom_types.PyShedsFACkwargsDict.__annotations__,
    }

    @staticmethod
    def _prep_fdr_for_pysheds(
        array: xr.DataArray,
    ) -> PyShedsInputDict:
        """Converts a three dimension (i.e. value = f(x, y)) xr.DataArray Flow Direction Raster into necessary pysheds inputs.

        Args:
            array: A 3-dimension array.

        Returns: A dict storing PyShed's relevant data formats of the following form
            {'input_array': param:array,
            'raster': pysheds.Raster(),
            'grid': pysheds.Grid()}
        """
        array.rio.write_transform()
        affine = array.rio.transform()

        # get nodata value
        nodata_val = array.rio.nodata
        array_np = array.values.astype(dtype=str(array.dtype)).squeeze()

        # make a mask for the grid object
        mask = array.astype('bool')
        mask = mask.where(array != array.rio.nodata, False).values

        view = ViewFinder(
            shape=array_np.shape,
            affine=affine,
            nodata=nodata_val,
            mask=mask,
        )

        raster_obj = PyShedsRaster(
            array_np,
            view,
        )

        # note: edits to this dictionary should be reflected in the PyShedsInputDict TypedDict instance
        out_dict = {
            'input_array': array,
            'raster': raster_obj,
            'grid': Grid().from_raster(raster_obj, affine=affine),
        }

        return out_dict

    @staticmethod
    def _pysheds_to_xarray(
        pysheds_io_dict: PyShedsInputDict,
        name: str = 'pysheds_output',
    ) -> xr.DataArray:
        """Backend function used to convert PySheds objects back into an xarray.DataArray."""

        array = xr.DataArray(
            pysheds_io_dict['raster'],
            coords=pysheds_io_dict['input_array'].squeeze().coords,
            name=name,
            attrs=pysheds_io_dict['input_array'].attrs,
        )
        return array

    @staticmethod
    def accumulate_flow(
        d8_fdr: Raster,
        upstream_pour_points: Optional[PourPointValuesDict] = None,
        weights: Optional[xr.DataArray] = None,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Create a Flow Accumulation Cell (FAC) raster from a ESRI format D8 Flow Direction Raster.

        NOTE: Replaces tools.tauFlowAccum() from V1 FCPGtools.

        Args:
            d8_fdr: A ESRI format D8 Flow Direction Raster (dtype=Int).
            upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
                and updated cell values as the second [1].
                This allows the FAC to be made with boundary conditions such as upstream basin pour points.
            weights: A grid defining the value to accumulate from each cell. Default is a grid of 1s.
            out_path: Defines a path to save the output raster.
            **kwargs: Can pass in optional pysheds.Grid.accumulation kwargs.

        Returns:
            The output Flow Accumulation Cells (FAC) raster.
        """
        d8_fdr = tools.load_raster(d8_fdr)
        d8_fdr = d8_fdr.where(
            (d8_fdr.values != d8_fdr.rio.nodata),
            0,
        )
        pysheds_input_dict = PyShedsEngine._prep_fdr_for_pysheds(d8_fdr)

        # prep kwargs to be passed into accumulate_flow()
        if 'kwargs' in kwargs.keys():
            kwargs = kwargs['kwargs']

        # add weights if necessary
        if weights is not None or upstream_pour_points is not None:
            if weights is not None:
                pass
            elif upstream_pour_points is not None:
                weights = xr.zeros_like(
                    d8_fdr,
                    dtype=np.dtype('float64'),
                ) + 1
                weights = tools.adjust_parameter_raster(
                    weights,
                    d8_fdr,
                    upstream_pour_points,
                )
            weights = PyShedsRaster(
                tools.make_fac_weights(
                    weights,
                    d8_fdr,
                    np.nan,
                ).values,
                pysheds_input_dict['raster'].viewfinder,
            )
        else:
            weights = None

        # apply accumulate function
        accumulate = pysheds_input_dict['grid'].accumulation(
            pysheds_input_dict['raster'],
            nodata_in=pysheds_input_dict['input_array'].rio.nodata,
            weights=weights,
            kwargs=kwargs,
        )

        # export back to DataArray
        out_raster = PyShedsEngine._pysheds_to_xarray(
            pysheds_io_dict={
                'grid': pysheds_input_dict['grid'],
                'raster': accumulate,
                'input_array': pysheds_input_dict['input_array'],
            },
            name='accumulate',
        )

        # convert out of bounds values to np.nan
        out_raster = out_raster.where(
            d8_fdr.values != d8_fdr.rio.nodata,
            out_raster.rio.nodata,
        )

        out_raster = utilities._change_nodata_value(
            out_raster,
            np.nan,
        )

        # save if necessary
        if out_path is not None:
            tools.save_raster(
                out_raster,
                out_path,
            )
        return out_raster

    @staticmethod
    def accumulate_parameter(
        d8_fdr: Raster,
        parameter_raster: Raster,
        upstream_pour_points: Optional[PourPointValuesDict] = None,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Create a parameter accumulation raster from a ESRI format D8 Flow Direction Raster and a parameter raster.

        A key aspect of this function is that the output DataArray will have dimensions matching param:parameter_raster.
        NOTE: Replaces tools.accumulateParam() from V1 FCPGtools.

        Args:
            d8_fdr: A ESRI format D8 Flow Direction Raster (dtype=Int).
            parameter_raster: A parameter raster aligned via tools.align_raster() with the us_fdr. 
                This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
            upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
                and updated cell values as the second [1].
                This allows the FAC to be made with boundary conditions such as upstream basin pour points.
            out_path: Defines a path to save the output raster.
            **kwargs: Can pass in optional pysheds.Grid.accumulation kwargs.

        Returns:
            The output parameter accumulation raster.
        """
        d8_fdr = tools.load_raster(d8_fdr)
        parameter_raster = tools.load_raster(parameter_raster)

        # add any pour point accumulation via utilities.tools.adjust_parameter_raster()
        if upstream_pour_points is not None:
            parameter_raster = tools.adjust_parameter_raster(
                parameter_raster,
                d8_fdr,
                upstream_pour_points,
            )

        # prep kwargs to be passed into accumulate_flow()
        if 'kwargs' in kwargs.keys():
            kwargs = kwargs['kwargs']

        # split if multi-dimensional
        if len(parameter_raster.shape) > 2:
            raster_bands = utilities._split_bands(parameter_raster)
        else:
            raster_bands = {(0, 0): parameter_raster}

        # create weighted accumulation rasters
        out_dict = {}
        for index_tuple, array in raster_bands.items():
            i, dim_name = index_tuple

            accumulated = PyShedsEngine.accumulate_flow(
                d8_fdr,
                upstream_pour_points=upstream_pour_points,
                weights=array,
                kwargs=kwargs,
            )
            out_dict[(i, dim_name)] = accumulated.copy()

        # re-combine into DataArray
        if len(out_dict.keys()) > 1:
            out_raster = utilities._combine_split_bands(out_dict)
        else:
            out_raster = list(out_dict.items())[0][1]

        # save if necessary
        if out_path is not None:
            tools.save_raster(
                out_raster,
                out_path,
            )

        return out_raster
