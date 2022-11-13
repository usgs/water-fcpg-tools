from typing import Union, List, Tuple, Dict
import os
from pathlib import Path
import xarray as xr
import numpy as np
import pandas as pd
import rioxarray as rio
from rasterio.enums import Resampling
import geopandas as gpd
from fcpgtools.types import Raster, Shapefile, RasterSuffixes, ShapefileSuffixes, \
    PourPointValuesDict

# CLIENT FACING I/O FUNCTIONS
def intake_raster(
    in_raster: Raster,
    ) -> xr.DataArray:
    """Used in the first line of most functions to make sure all inputs are DataArray"""
    if isinstance(in_raster, xr.DataArray):
        return in_raster.squeeze()
    elif isinstance(in_raster, os.PathLike):
        return rio.open_rasterio(in_raster).squeeze()

def intake_shapefile(
    in_shapefile: Shapefile,
    ) -> gpd.GeoDataFrame:
    """Used in the first line of most functions to make sure all shapefile data is in a GeoDataFrame"""
    if isinstance(in_shapefile, gpd.GeoDataFrame):
        return in_shapefile
    elif isinstance(in_shapefile, os.PathLike):
        return gpd.read_file(in_shapefile)

def save_raster(
    out_raster: xr.DataArray,
    out_path: Union[str, os.PathLike],
    ) -> None:
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        print(f'WARNING: Cannot overwrite {out_path}!')
        return None
    try:
        out_raster.rio.to_raster(out_path)
    except Exception as e:
        print(e)

def save_shapefile(
    out_shapefile: gpd.GeoDataFrame,
    out_path: Union[str, os.PathLike]
    ) -> None:
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        print(f'WARNING: Cannot overwrite {out_path}!')
        return None
    try:
        out_shapefile.to_file(out_path)
    except Exception as e:
        print(e)

def id_d8_format(
    raster: Raster,
    ) -> str:
    raster = intake_raster(raster)
    uniques = np.unique(raster.values)
    if np.max(uniques) > 8: return 'esri'
    elif np.max(uniques) <= 8: return 'taudem'
    else: return print('ERROR: Cant recognize D8 Flow Direction Raster format '
    'as either ESRI or TauDEM. Please use the param:in_format for pyfunc:convert_fdr_formats()')

# BACK-END FACING UTILITY FUNTIONS
def _intake_ambigous(
    in_data: Union[Raster, Shapefile],
    ) -> Union[xr.DataArray, gpd.GeoDataFrame]:
    """Somewhat less performant intake function when the input can be either a Raster or Shapefile"""
    if isinstance(in_data, os.PathLike):
        if in_data.suffix in RasterSuffixes:
            return intake_raster(in_data)
        elif in_data.suffix in ShapefileSuffixes:
            return intake_shapefile(in_data)
    elif isinstance(in_data, xr.DataArray) or isinstance(in_data, gpd.GeoDataFrame):
        return in_data

def _get_crs(
    out_crs: Union[Raster, Shapefile],
    ) -> str:
    crs_data = _intake_ambigous(out_crs)

    if isinstance(crs_data, xr.DataArray):
        return crs_data.rio.crs.to_wkt()
    elif isinstance(crs_data, gpd.GeoDataFrame):
        return crs_data.crs.to_wkt()

def _verify_dtype(
    raster: xr.DataArray,
    value: Union[float, int],
    ) -> bool:
    dtype = str(raster.dtype)
    if 'float' in dtype:
        return True
    elif not isinstance(value, int):
        return False
    else:
        if 'int8' in dtype and value > 255:
            return False
        #TODO: How best to handle other int dtype? What are the value ranges.
        return True

def _update_cell_value_(
    raster: xr.DataArray,
    coords: Tuple[float, float],
    value: Union[float, int],
    ) -> xr.DataArray:
    """
    Underlying function called in update_cell_values() to update a DataArray by x,y coordinates.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :param coords: (tuple) coordinate as (lat:float, lon:float) of the cell to be updated.
    :param value: (float or int) new value to give the cell.
    :returns: param:in_raster with the updated cell value as a xarray DataArray object.
    """
    if _verify_dtype(raster, value):
        raster.loc[{'x': coords[0], 'y': coords[1]}] = value
        return raster
    else:
        #TODO: Handle exceptions
        print(f'ERROR: Value {value} does not match DataArray dtype = {raster.dtype}')
        return raster

def _format_nodata(
    in_raster: xr.DataArray,
    ) -> xr.DataArray:
    """
    If in_raster.rio.nodata is None, a nodata value is added.
    For dtype=float -> np.nan, for dtype=int -> 255.
    """
    if in_raster.rio.nodata is None:
        og_dtype = str(in_raster.dtype)
        if 'float' in og_dtype: nodata_value = np.nan
        elif 'int' in og_dtype: nodata_value = 255
        if 'int8' in og_dtype:
            if np.min(np.unique(in_raster.values)) < 0: in_raster = in_raster.astype('int16')
            else: in_raster = in_raster.astype('uint8')

        in_raster.rio.write_nodata(
            nodata_value,
            inplace=True,
            ) 
    return in_raster

def _split_bands(
    in_raster: xr.DataArray,
    ) -> Dict[Tuple[int, Union[int, str, np.datetime64]], xr.DataArray]:
    """
    Splits a 3 dimensional xr.DataArray into 2D arrays indexed by either an int or string dimension label.
    :param in_raster: (xr.DataArray) a raster with a 3rd dimension (i.e. band, or f(x, y, t)). 
    :returns: (dict) a dictionary with the int or string 3rd dimension label as keys, storing 2D data arrays.
    """
    if len(in_raster.shape) > 3:
        print(f'ERROR: param:in_raster (xr.DataArray) has 4 dimensions (shape={in_raster.shape}).'
        ' Please use a 2 or 3 dimension xr.DataArray.')
        raise TypeError
    if len(in_raster.shape) < 3:
        print('WARNING: param:in_raster was expected to have 3-dimensions, but only has two.')
        return {0: in_raster}
    
    # if 3 dimensions are passed, pull out the first dimension index values
    dim_index = list(in_raster[in_raster.dims[0]].values)
    index_tuples = []
    for i, index_val in enumerate(dim_index):
        index_tuples.append((i, index_val))
    
    out_dict = {}
    for index_tuple in index_tuples:
        out_dict[index_tuple] = in_raster.sel(
            {in_raster.dims[0]: index_tuple[-1]},
            )
    return out_dict

def _combine_split_bands(
    split_dict: Dict[Tuple[int, Union[int, str, np.datetime64]], xr.DataArray],
    ) -> xr.DataArray:

    index_name = 'band'
    if isinstance(list(split_dict.keys())[0][-1], np.datetime64): index_name = 'time'

    # re-create the 4th dimension index and concat
    index = pd.Index(
        [i[-1] for i in list(split_dict.keys())],
        name=index_name)
    return xr.concat(
        objs=split_dict.values(),
        dim=index,
        )

def _update_parameter_raster(
    parameter_raster: xr.DataArray,
    upstream_pour_points: PourPointValuesDict,
    ) -> xr.DataArray:
    #TODO: Decide when to find downstream cell, probs best here?
    
    # pull in pour point data
    pour_point_ids = upstream_pour_points['pour_point_ids']
    pour_point_coords = upstream_pour_points['pour_point_coords']
    pour_point_values = upstream_pour_points['pour_point_values']

    if len(parameter_raster.shape) == 2:
        # make update cell values list
        update_cells_list = []
        for i, coords in pour_point_coords:
            value = pour_point_values[i][0]
            update_cells_list.append(
                (coords, value)
            )

        parameter_raster = update_cell_values(
            in_raster=parameter_raster,
            update_points=update_cells_list,
            )
    else:
        dim_index = parameter_raster[parameter_raster.dims[0]].values
        for i, value in enumerate(dim_index):
            slice = parameter_raster.isel(
                {parameter_raster.dims[0]: i}
                )

            # make update cell values list
            update_cells_list = []
            for j, coords in pour_point_coords:
                value = pour_point_values[j][i]
                update_cells_list.append(
                    (coords, value)
                )

            #TODO: verify that this behavior works well
            slice = update_cell_values(
                in_raster=slice,
                update_points=update_cells_list,
                )
    return parameter_raster


# FRONT-END/CLIENT FACING UTILITY FUNTIONS
def clip(
    in_raster: Raster,
    match_raster: Raster = None,
    match_shapefile: Shapefile = None,
    custom_bbox: list = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Clips a raster to the rectangular extent (aka bounding box) of another raster (or shapefile).
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param match_raster: (xr.DataArray or str raster path) if defined, in_raster is
        clipped to match the extent of match_raster.
    :param match_shapefile: (str path or GeoDataFame, default=None) a shapefile that is used to define
        the output extent if match_raster == None.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param custom_bbox: (list, default=None) a list with bounding box coordinates that define the output
        extent if match_raster == None. Coordinates must be of the form [minX, minY, maxX, maxY].
        Note: Using this parameter assumes that coordinates match the CRS of param:in_raster.
    :returns: (xr.DataArray) the clipped raster as a xarray DataArray object.
    """
    in_raster = intake_raster(in_raster)

    if match_raster is not None:
        match_raster = intake_raster(match_raster)
        crs = match_raster.rio.crs.to_wkt()
        bbox = list(match_raster.rio.bounds())
    elif match_shapefile is not None:
        match_shapefile = intake_shapefile(match_shapefile)
        crs = match_shapefile.crs.to_wkt()
        bbox = match_shapefile.geometry.total_bounds
    elif custom_bbox is not None:
        crs = in_raster.rio.crs.to_wkt()
        bbox = custom_bbox
    
    out_raster = in_raster.rio.clip_box(
        minx=bbox[0],
        miny=bbox[1],
        maxx=bbox[2],
        maxy=bbox[3],
        crs=crs,
        )
    if out_path is not None:
        save_raster(out_raster, out_path)

    return out_raster

def reproject_raster(
    in_raster: Raster,
    out_crs: Union[Raster, Shapefile] = None,
    wkt_string: str = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Reprojects a raster to match another rasters Coordinate Reference System (CRS), or a custom CRS.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param out_crs: (xr.DataArray, gpd.GeoDataFrame, or string file path) the output CRS,
        defined by either copying another raster or shapefile's CRS.
    :param wkt_string: (str, valid CRS WKT - default is None) allows the user to pass in a custom WKT string.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the reprojected raster as a xarray DataArray object.
    """
    in_raster = intake_raster(in_raster)
    if out_crs is not None:
        out_crs = _get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
    else:
        #TODO: Update exceptions
        print('Must pass in either param:out_crs or param:wkt_string')
        return None
    
    # set nodata value, change dtype if necessary
    in_raster = _format_nodata(in_raster)
        
    out_raster = in_raster.rio.reproject(
        out_crs,
        nodata=in_raster.rio.nodata,
        kwargs={
            'dst_nodata': in_raster.rio.nodata,
            },
        )

    if out_path is not None:
        save_raster(out_raster, out_path)
    return out_raster

def reproject_shapefile(
    in_shapefile: Shapefile,
    out_crs: Union[Raster, Shapefile] = None,
    wkt_string: str = None,
    out_path: str = None,
    ) -> xr.DataArray:
    in_shapefile = intake_raster(in_shapefile)
    if out_crs is not None:
        out_crs = _get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
    else:
        #TODO: Update exceptions
        print('Must pass in eitehr param:out_crs or param:wkt_string')
        return None

    out_shapefile = in_shapefile.to_crs(out_crs)
    if out_path is not None:
        save_shapefile(out_shapefile, out_path)
    return out_shapefile

def resample(
    in_raster: Raster,
    match_raster: Raster,
    method: str = 'bilinear',
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Resamples a raster to match another raster's cell size, or a custom cell size.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param match_raster: (xr.DataArray or str raster path) if defined, in_raster is
        resampled to match the cell size of match_raster.
    :param method: (str, default=bilinear) a valid resampling method from rasterio.enums.Resample.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the resampled raster as a xarray DataArray object.
    """
    in_raster = intake_raster(in_raster)
    match_raster = intake_raster(match_raster)

    # set nodata value, change dtype if necessary
    in_raster = _format_nodata(in_raster)

    try:
        out_raster = in_raster.rio.reproject(
        in_raster.rio.crs,
        shape=(match_raster.rio.height, match_raster.rio.width),
        resampling=getattr(Resampling, method),
        kwargs={
        'dst_nodata': in_raster.rio.nodata,
            },
        )

    except AttributeError:
        #TODO: handle exceptions
        real_methods = vars(Resampling)['_member_names_']
        print(f'Resampling method {method} is invalid! Please select from {real_methods}')

    if out_path is not None:
        save_raster(out_raster, out_path)

    return out_raster

def sample_raster(
    raster: xr.DataArray,
    coords: Tuple[float, float],
    ) -> Union[float, int]:
    """
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :param coords: (tuple) coordinate as (lat:float, lon:float) of the cell to be sampled.
    :returns: (float or int) the cell value at param:coords.
    """
    return raster.sel({'x': coords[0],
            'y': coords[1]}).values.item(0)

def get_min_cell(
    raster: xr.DataArray,
    ) -> Tuple[Tuple[float, float], Union[float, int]]:
    """
    Get the minimum cell coordinates + value from a single band raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (list) a list (len=2) with the min cell's coordinate tuple [0] and value [1]
        i.e., [coords:tuple, value:Union[float, int]].
    """
    xmin_index = raster.argmin(dim=['x', 'y'])['x'].data.item(0)
    ymin_index = raster.argmin(dim=['x', 'y'])['y'].data.item(0)

    min_slice = raster.isel({'x': xmin_index,
                'y': ymin_index})
    return [(min_slice.x.values.item(0), min_slice.y.values.item(0)), min_slice.values.item(0)]

def get_max_cell(
    raster: xr.DataArray,
    ) -> Tuple[Tuple[float, float], Union[float, int]]:
    """
    Get the maximum cell coordinates + value from a raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (list) a list (len=2) with the max cell's coordinate tuple [0] and value [1]
        i.e., [coords:tuple, value:Union[float, int, np.array]].
    """
    xmax_index = raster.argmax(dim=['x', 'y'])['x'].data.item(0)
    ymax_index = raster.argmax(dim=['x', 'y'])['y'].data.item(0)

    max_slice = raster.isel({'x': xmax_index,
                'y': ymax_index})
    return [(max_slice.x.values.item(0),
            max_slice.y.values.item(0)),
            max_slice.values.item(0)]

def update_cell_values(
    in_raster: Union[xr.DataArray, str],
    update_points: List[Tuple[Tuple[float, float], Union[float, int]]],
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Update a specific raster cell's value based on it's coordindates. This is primarily used
    to add upstream accumulation values as boundary conditions before making a FAC or FCPG.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param update_points: (list) a list of tuples storing cell coordinates updated values
        of the form [((x_coord:float, y_coord:float), updated_value),...].
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: param:in_raster with the updated cell value as a xarray DataArray object.
    """
    out_raster = intake_raster(in_raster)

    for update_tuple in update_points:
        _update_cell_value_(
            out_raster,
            coords=update_tuple[0],
            value=update_tuple[-1],
            )

    if out_path is not None:
        save_raster(out_raster, out_path)

    return out_raster

# CIRCLE BACK TO THESE, MAY NOT BE NECESSARY?
def verify_extent(
    raster: xr.DataArray,
    coords: tuple,
    ) -> bool:
    """
    Returns True if coordinates are contained within a given raster.
    :param raster: (xr.DataArray or str raster path) a georeferenced raster.
    :param coords: (tuple) the input (lat:float, lon:float) to verify.
    :returns: boolean. True if param:coords is w/in the spatial extent of param:raster.
    """
    # Note: this function should be used within other functions that query
    # a raster using lat/long coordinates.
    # 1. get raster bbox coorindates
    # 2. see if coords is within the bbox, return a boolean
    raise NotImplementedError

def minimize_extent(
    in_raster: Union[xr.DataArray, str],
    nodata_value: Union[float, int] = None,
    ) -> xr.DataArray:
    """
    Minimizes the extent of a raster to the bounding box of all non-nodata cells.
    Useful after raster operations where extents don't match and nodata values are propageted forwards.
    :param in_raster: (xr.DataArray or str raster path) the input raster.
    :param nodata_value: (float->np.nan or int) if the nodata value for param:in_raster is not in the metadata,
        set this parameter to equal the cell value storing nodata (i.e., np.nan or -999).
    :returns: (xr.DataArray) the clipped output raster as a xarray DataArray object.
    """
    # if no nodata values -> return in_raster
    # else return the minimum extent
    raise NotImplementedError

def change_nodata(
    in_raster: Union[xr.DataArray, str],
    nodata_value: Union[float, int],
    out_path: str = None,
    convert_dtype: bool = True,
    ) -> xr.DataArray:
    """
    Update a specific raster nodata value.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param nodata_value: (float or int) new value to give nodata cells before saving.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param convert_dtype: (bool, default=True) if param:nodata_value is non-compatible
        with in_raster's dtype, a dtype conversion is default unless False.
    :returns: param:in_raster with the updated nodata values as a xarray DataArray object.
    """
    # Note for dev: we need to understand xarray's handling of nodata values
    raise NotImplementedError

def change_dtype(
    in_raster: Union[xr.DataArray, str],
    out_dtype: str,
    out_path: str = None,
    allow_rounding: bool = False,
    ) -> xr.DataArray:
    """
    Change a rasters datatype to another valid xarray datatype.
    :param in_raster: (xr.DataArray or str path) input raster.
    :param out_dtype: (str) a valid xarray datatype string (i.e., float64, int64...).
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param allow_rounding: (bool, default=False) allows rounding of float -> int.
    :returns: (xr.DataArray) the raster with it's dtype changed.
    """
    raise NotImplementedError

def get_raster_bbox(
    raster: xr.DataArray,
    ) -> Tuple[float, float, float, float]:
    """
    Get bounding box coordinates of a raster.
    :param raster: (xr.DataArray or str raster path) a georeferenced raster.
    :returns: (Tuple)  with bounding bbox coordinates - [minX, minY, maxX, maxY]
    """
    # this function is used to in verify_extent() as well as clip().
    # MAY NOT BE NECESSARY
    raise NotImplementedError

def get_shp_bbox(
    shp: Union[str, gpd.GeoDataFrame],
    ) -> list:
    """
    Get bbox coordinates of a shapefile.
    :param shp: (geopandas.GeoDataFrame or str shapefile path) a georeferenced shapefile.
    :returns: (list) list with bounding bbox coordinates - [minX, minY, maxX, maxY]
    """
    # MAY NOT BE NECESSARY
    raise NotImplementedError



