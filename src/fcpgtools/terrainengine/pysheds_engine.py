import xarray as xr
import numpy as np
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster
from pysheds.view import ViewFinder
from pathlib import Path
from typing import List, Dict, TypedDict, Union
from fcpgtools.types import Raster, PyShedsInputDict, PourPointValuesDict
from fcpgtools.utilities import load_raster, _split_bands, _combine_split_bands, \
    adjust_parameter_raster, save_raster, _verify_shape_match, change_nodata_value
from fcpgtools.tools import make_fac_weights


# UNDERLYING FUNCTIONS TO IMPORT/EXPORT DATA FROM PYSHEDS OBJECTS
def _make_new_nodata(
    array: xr.DataArray,
    ) -> xr.DataArray:
    #TODO: Figure out best way to deal with this
    return (array.data.squeeze().astype('int16'), 0)

def _xarray_to_pysheds(
    array: xr.DataArray,
    ) -> PyShedsInputDict:
    """
    Converts a three dimension (i.e. value = f(x, y)) xr.DataArray into a pysheds inputs.
    :param array: (xr.DataArray) a 3-dimension array.
    :returns: (dict) a dict storing PyShed's relevant data formats of the following form:
        {'input_array': param:array,
        'raster': pysheds.Raster(),
        'grid': pysheds.Grid()}
    """
    array.rio.write_transform()
    affine = array.rio.transform()
    
    # nodata must be defined for pysheds
    if array.rio.nodata is None:
        array_np, nodata_val = _make_new_nodata(array)
    else:
        nodata_val = array.rio.nodata
        array_np = array.values.astype(dtype=str(array.dtype)).squeeze()

    # make a mask for the grid object
    mask = array.astype('bool')
    mask = mask.where(array != array.rio.nodata, False).values
    
    view = ViewFinder(shape=array_np.shape,
                      affine=affine,
                      nodata=nodata_val,
                      mask=mask,
                      )

    raster_obj = PyShedsRaster(array_np, view)
    
    # note: edits to this dictionary should be reflected in the PyShedsInputDict TypedDict instance
    out_dict = {
        'input_array': array,
        'raster': raster_obj,
        'grid': Grid().from_raster(raster_obj, affine=affine),
        }
    
    return out_dict

def _pysheds_to_xarray(
    pysheds_io_dict: PyShedsInputDict,
    name: str = 'pysheds_output',
    ) -> xr.DataArray:

    array = xr.DataArray(
        pysheds_io_dict['raster'],
        coords=pysheds_io_dict['input_array'].squeeze().coords,
        name=name,
        attrs=pysheds_io_dict['input_array'].attrs,
        )
    return array

# CLIENT FACING PROTOCOL IMPLEMENTATIONS
def accumulate_flow(
    d8_fdr: Raster, 
    weights: xr.DataArray = None,
    upstream_pour_points: PourPointValuesDict = None,
    out_path: Union[str, Path] = None,
    ) -> xr.DataArray:

    d8_fdr = load_raster(d8_fdr)
    d8_fdr = d8_fdr.where(
        (d8_fdr.values != d8_fdr.rio.nodata),
        0,
        )
    pysheds_input_dict = _xarray_to_pysheds(d8_fdr)

    if weights is not None or upstream_pour_points is not None:
        # add weights if necessary
        if weights is not None: weights = weights
        #TODO: Implement upstream pour points using weighting grid!
        elif upstream_pour_points is not None:
            weights = xr.zeros_like(
                d8_fdr,
                dtype=np.dtype('float64'),
                ) + 1
            weights = adjust_parameter_raster(
                weights,
                d8_fdr,
                upstream_pour_points,
                )
        weights = PyShedsRaster(
            make_fac_weights(
                weights,
                d8_fdr,
                np.nan,
                ).values,
            pysheds_input_dict['raster'].viewfinder,
            )
    else: weights = None

    # apply accumulate function
    accumulate = pysheds_input_dict['grid'].accumulation(
        pysheds_input_dict['raster'], 
        nodata_in=pysheds_input_dict['input_array'].rio.nodata,
        weights=weights,
        )

    # export back to DataArray
    out_raster = _pysheds_to_xarray(
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

    out_raster = change_nodata_value(
        out_raster,
        np.nan
        )

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)
    
    return out_raster

def accumulate_parameter( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: PourPointValuesDict = None,
    out_path: Union[str, Path] = None,
    **kwargs,
    ) -> xr.DataArray:

    d8_fdr = load_raster(d8_fdr)
    parameter_raster = load_raster(parameter_raster)

    # add any pour point accumulation via utilities.adjust_parameter_raster()
    if upstream_pour_points is not None: parameter_raster = adjust_parameter_raster(
        parameter_raster,
        d8_fdr,
        upstream_pour_points,
        )

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2:
        raster_bands = _split_bands(parameter_raster)
    else:
        raster_bands = {(0, 0): parameter_raster}

    # create weighted accumulation rasters
    out_dict = {}
    for index_tuple, array in raster_bands.items():
        i, dim_name = index_tuple

        accumulated = accumulate_flow(
            d8_fdr,
            upstream_pour_points=upstream_pour_points,
            weights=array,
            )
        out_dict[(i, dim_name)] = accumulated.copy()

    # re-combine into DataArray
    if len(out_dict.keys()) > 1:
        out_raster =  _combine_split_bands(out_dict)
    else: out_raster =  list(out_dict.items())[0][1] 

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)
    
    return out_raster

    


