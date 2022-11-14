import xarray as xr
import numpy as np
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster
from pysheds.view import ViewFinder
from typing import List, Dict, TypedDict
from fcpgtools.types import Raster, PyShedsInputDict
from fcpgtools.utilities import intake_raster, _split_bands, _combine_split_bands, \
    _update_parameter_raster, save_raster

# Grid.add_gridded_data(self, data, data_name, affine=None, shape=None, crs=None,
#                         nodata=None, mask=None, metadata={}):

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
    view = ViewFinder(shape=array_np.shape,
                      affine=affine,
                      nodata=nodata_val)
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

#TODO: figure out concating to re-build multi-dimensions

# CLIENT FACING PROTOCOL IMPLEMENTATIONS
def fac_from_fdr(
            d8_fdr: Raster, 
            upstream_pour_points: List = None,
            out_path: str = None,
            **kwargs,
        ) -> xr.DataArray:

    d8_fdr = intake_raster(d8_fdr)
    pysheds_input_dict = _xarray_to_pysheds(d8_fdr)

    # add weights if necessary
    if kwargs == {}: weights = None
    elif 'weights' in kwargs['kwargs'].keys(): weights = kwargs['kwargs']['weights']
    else: weights = None

    # apply accumulate function
    accumulate = pysheds_input_dict['grid'].accumulation(
        pysheds_input_dict['raster'],
        nodata_in=pysheds_input_dict['input_array'].rio.nodata,
        weights=weights,
        )

    # export back to DataArray
    return _pysheds_to_xarray(
        pysheds_io_dict={
            'grid': pysheds_input_dict['grid'],
            'raster': accumulate,
            'input_array': pysheds_input_dict['input_array'],
            },
        name='accumulate',
        )

def parameter_accumulate( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: List = None,
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:
    
    d8_fdr = intake_raster(d8_fdr)
    parameter_raster = intake_raster(parameter_raster)

    # add any pour point accumulation via utilities._update_parameter_raster()
    if upstream_pour_points is not None: parameter_raster = _update_parameter_raster(
        parameter_raster,
        upstream_pour_points,
        )

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2:
        raster_bands = _split_bands(parameter_raster)
    else:
        dim_name = list(parameter_raster[parameter_raster.dims[0]].values)[0]
        raster_bands = {(0, dim_name): parameter_raster}

    # create weighted accumulation rasters
    out_dict = {}
    for index_tuple, array in raster_bands.items():
        i, dim_name = index_tuple
        #TODO: switch to where 0s are added only for where there IS FDR data
        # array = array.fillna(0)
        param_input_dict = _xarray_to_pysheds(array)

        accumulated = fac_from_fdr(
            d8_fdr,
            upstream_pour_points=upstream_pour_points,
            kwargs={'weights': param_input_dict['raster']},
            )
        out_dict[(i, dim_name)] = accumulated

    # re-combine into DataArray
    if len(out_dict.keys()) > 1:
        out_raster =  _combine_split_bands(out_dict)
    else: out_raster =  list(out_dict.items())[0][1] 

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)
    
    return out_raster

    


