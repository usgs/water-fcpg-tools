import xarray as xr
import numpy as np
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster
from pysheds.view import ViewFinder
from typing import List, Dict, TypedDict
from fcpgtools.types import Raster, PyShedsInputDict

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
    Converts a three dimension (i.e. value = f(x, y)) xr.DataArray into a pysheds Grid.
    """
    array.rio.write_transform
    affine = array.rio.transform()
    
    # nodata must be defined for pysheds
    if array.rio.nodata is None:
        array_np, nodata_val = _make_new_nodata(array)
    else:
        nodata_val = array.rio.nodata
        array_np = array.data.squeeze()  
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

def _pysheds_to_xarray(raster, original_array) -> xr.DataArray:
    array = xr.DataArray(
        raster,
        coords=original_array.squeeze().coords,
        name='fac_raster',
        attrs={'dtype': original_array.dtype,
            'spatial_ref': original_array.spatial_ref},
        )
    return array

# CLIENT FACING PROTOCOL IMPLEMENTATIONS
def fac_from_fdr(
            d8_fdr: Raster, 
            upstream_pour_points: List = None,
            out_path: str = None,
            **kwargs,
        ) -> xr.DataArray:

    #TODO: PICK BACK UP HERE
    d8_grid = Grid.add_gridded_data()
    raise NotImplementedError
