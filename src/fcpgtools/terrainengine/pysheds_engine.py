import xarray as xr
import numpy as np
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster
from pysheds.view import ViewFinder
from typing import List, Dict, TypedDict
from fcpgtools.types import Raster, PyShedsInputDict
from fcpgtools.utilities import intake_raster, _split_bands, _combine_split_bands, \
    update_parameter_raster, save_raster, _verify_shape_match, _replace_nodata_value
from fcpgtools.tools import prep_parameter_grid


# UNDERLYING FUNCTIONS TO IMPORT/EXPORT DATA FROM PYSHEDS OBJECTS
def _make_new_nodata(
    array: xr.DataArray,
    ) -> xr.DataArray:
    #TODO: Figure out best way to deal with this
    return (array.data.squeeze().astype('int16'), 0)

def _xarray_to_pysheds(
    array: xr.DataArray,
    is_fdr: bool,
    ) -> PyShedsInputDict:
    """
    Converts a three dimension (i.e. value = f(x, y)) xr.DataArray into a pysheds inputs.
    :param array: (xr.DataArray) a 3-dimension array.
    :param is_fdr: (bool) controls whether a nodata mask is writted in the grid object
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
    if is_fdr:
        mask = array.astype('bool')
        mask = mask.where(array != array.rio.nodata, False).values
    else: mask = None
    
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
    name: str = 'pysheds_output'
    ) -> xr.DataArray:

    array = xr.DataArray(
        pysheds_io_dict['raster'],
        coords=pysheds_io_dict['input_array'].squeeze().coords,
        name=name,
        attrs=pysheds_io_dict['input_array'].attrs,
        )
    return array

# CLIENT FACING PROTOCOL IMPLEMENTATIONS
def fac_from_fdr(
    d8_fdr: Raster, 
    weights: xr.DataArray = None,
    upstream_pour_points: List = None,
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:

    d8_fdr = intake_raster(d8_fdr)
    d8_fdr = d8_fdr.where(
        (d8_fdr.values != d8_fdr.rio.nodata),
        0,
        )
    pysheds_input_dict = _xarray_to_pysheds(d8_fdr, is_fdr=True)

    if weights is not None or upstream_pour_points is not None:
        # add weights if necessary
        if weights is not None: weights = weights
        #TODO: Implement upstream pour points using weighting grid!
        elif upstream_pour_points is not None:
            weights = xr.zeros_like(
                d8_fdr,
                dtype=np.dtype('float64'),
                ) + 1
            weights = update_parameter_raster(
                weights,
                upstream_pour_points,
                )
            weights = _xarray_to_pysheds(
                _prep_parameter_grid(
                    weights,
                    d8_fdr,
                    np.nan,
                    ),
                is_fdr=False,
                )['raster']
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

    out_raster = _replace_nodata_value(
        out_raster,
        np.nan
        )

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)
    
    return out_raster

def parameter_accumulate( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: List = None,
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:
    
    d8_fdr = intake_raster(d8_fdr)
    parameter_raster = intake_raster(parameter_raster)

    # add any pour point accumulation via utilities.update_parameter_raster()
    if upstream_pour_points is not None: parameter_raster = update_parameter_raster(
        parameter_raster,
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
        #TODO: switch to where 0s are added only for where there IS FDR data
        param_input_dict = _xarray_to_pysheds(
            _prep_parameter_grid(
                array,
                d8_fdr,
                array.rio.nodata,
                ),
            is_fdr=False,
            )

        accumulated = fac_from_fdr(
            d8_fdr,
            upstream_pour_points=upstream_pour_points,
            weights=param_input_dict['raster'],
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

    


