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
    PourPointValuesDict, D8ConversionDicts

# CLIENT FACING I/O FUNCTIONS
def load_raster(
    in_raster: Raster,
    ) -> xr.DataArray:
    """Used in the first line of most functions to make sure all inputs are DataArray w/ valid nodata"""
    if isinstance(in_raster, xr.DataArray):
        return _format_nodata(in_raster.squeeze())
    elif isinstance(in_raster, os.PathLike):
        return _format_nodata(rio.open_rasterio(in_raster).squeeze())

def load_shapefile(
    in_shapefile: Shapefile,
    ) -> gpd.GeoDataFrame:
    """Used in the first line of most functions to make sure all shapefile data is in a GeoDataFrame"""
    if isinstance(in_shapefile, gpd.GeoDataFrame):
        return in_shapefile
    elif isinstance(in_shapefile, os.PathLike):
        return gpd.read_file(in_shapefile)

def save_raster(
    out_raster: xr.DataArray,
    out_path: Union[str, Path],
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
    raster = load_raster(raster)
    uniques = np.unique(raster.values)
    if np.max(uniques) > 8: return 'esri'
    elif np.max(uniques) <= 8: return 'taudem'
    else: return print('ERROR: Cant recognize D8 Flow Direction Raster format '
    'as either ESRI or TauDEM. Please use the param:in_format for pyfunc:convert_fdr_formats()')

# CLIENT FACING UTILITY FUNTIONS
def adjust_parameter_raster(
    parameter_raster: Raster,
    d8_fdr: Raster,
    upstream_pour_points: PourPointValuesDict,
    ) -> xr.DataArray:

    # pull in data
    parameter_raster = load_raster(parameter_raster)
    d8_fdr = load_raster(d8_fdr)

    # pull in pour point data
    pour_point_coords = upstream_pour_points['pour_point_coords']
    pour_point_values = upstream_pour_points['pour_point_values']

    # update values iteratively
    for i, coords in enumerate(pour_point_coords):
        values_list = pour_point_values[i]

        # get downstream coordinates
        ds_coords = find_downstream_cell(
            d8_fdr,
            coords,
            )

        # verify coverage
        if not _verify_coords_coverage(
            parameter_raster,
            ds_coords,
            ):
            print(f'WARNING: Cell downstream from pour point coords={coords} is out of bounds -> skipped!')
            continue

        if len(parameter_raster.shape) == 2: 
            parameter_raster = update_raster_values(
                in_raster=parameter_raster,
                update_points=[(ds_coords, values_list[0])],
                )
        else:
            dim_index_values = parameter_raster[parameter_raster.dims[0]].values
            for band_index, value in enumerate(dim_index_values):
                parameter_raster[band_index,:,:] = update_raster_values(
                    in_raster=parameter_raster[band_index,:,:],
                    update_points=[(ds_coords, values_list[band_index])],
                    )
    return parameter_raster

def clip(
    in_raster: Raster,
    match_raster: Raster = None,
    match_shapefile: Shapefile = None,
    custom_bbox: list = None,
    out_path: Union[str, Path] = None,
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
    in_raster = load_raster(in_raster)

    if match_raster is not None:
        match_raster = load_raster(match_raster)
        crs = match_raster.rio.crs.to_wkt()
        bbox = match_raster.rio.bounds()
    elif match_shapefile is not None:
        match_shapefile = load_shapefile(match_shapefile)
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
    resolution: Union[float, Tuple[float, float]] = None,
    wkt_string: str = None,
    out_path: Union[str, Path] = None,
    ) -> xr.DataArray:
    """
    Reprojects a raster to match another rasters Coordinate Reference System (CRS), or a custom CRS.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param out_crs: (xr.DataArray, gpd.GeoDataFrame, or string file path) the output CRS,
        defined by either copying another raster or shapefile's CRS.
    :param resolution: (float or Tuple[float, float], default=None) allows the output resolution to be overriden.
    :param wkt_string: (str, valid CRS WKT - default is None) allows the user to pass in a custom WKT string.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the reprojected raster as a xarray DataArray object.
    """
    in_raster = load_raster(in_raster)
    if out_crs is not None:
        out_crs = _get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
        resolution = None
    else:
        #TODO: Update exceptions
        print('Must pass in either param:out_crs or param:wkt_string')
        return None
    
    out_raster = in_raster.rio.reproject(
        out_crs,
        resolution=resolution,
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
    out_path: Union[str, Path] = None,
    ) -> xr.DataArray:
    in_shapefile = load_raster(in_shapefile)
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
    method: str = 'nearest',
    out_path: Union[str, Path] = None,
    ) -> xr.DataArray:
    """
    Resamples a raster to match another raster's cell size, or a custom cell size.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param match_raster: (xr.DataArray or str raster path) if defined, in_raster is
        resampled to match the cell size of match_raster.
    :param method: (str, default=nearest) a valid resampling method from rasterio.enums.Resample.
        NOTE: Do not use any averaging resample methods when working with a categorical raster!
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the resampled raster as a xarray DataArray object.
    """
    in_raster = load_raster(in_raster)
    match_raster = load_raster(match_raster)

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

def query_point(
    raster: xr.DataArray,
    coords: Tuple[float, float],
    ) -> Union[float, int]:
    """
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :param coords: (tuple) coordinate as (lat:float, lon:float) of the cell to be sampled.
    :returns: (float or int) the cell value at param:coords.
    """
    #TODO: verify this works well
    return raster.sel({'x': coords[0],
        'y': coords[1]}).values.item(0)

def get_min_cell(
    raster: xr.DataArray,
    ) -> Tuple[float, float]:
    """
    Get the minimum cell coordinates + value from a single band raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (tuple) with the min cell's x, y coordinates.
    """
    xmin_index = raster.argmin(dim=['x', 'y'])['x'].data.item(0)
    ymin_index = raster.argmin(dim=['x', 'y'])['y'].data.item(0)

    min_slice = raster.isel({'x': xmin_index,
                'y': ymin_index})
    return (min_slice.x.values.item(0),
            min_slice.y.values.item(0))

def get_max_cell(
    raster: xr.DataArray,
    ) -> Tuple[float, float]:
    """
    Get the maximum cell coordinates + value from a raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (tuple) with the max cell's x, y coordinates.
    """
    xmax_index = raster.argmax(dim=['x', 'y'])['x'].data.item(0)
    ymax_index = raster.argmax(dim=['x', 'y'])['y'].data.item(0)

    max_slice = raster.isel({'x': xmax_index,
                'y': ymax_index})
    return (max_slice.x.values.item(0),
            max_slice.y.values.item(0))

def update_raster_values(
    in_raster: Union[xr.DataArray, str],
    update_points: List[Tuple[Tuple[float, float], Union[float, int]]],
    out_path: Union[str, Path] = None,
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
    out_raster = load_raster(in_raster)

    for update_tuple in update_points:
        _update_cell_value_(
            out_raster,
            coords=update_tuple[0],
            value=update_tuple[-1],
            )

    if out_path is not None:
        save_raster(out_raster, out_path)

    return out_raster

def change_nodata_value(
    in_raster: xr.DataArray,
    new_nodata: Union[float, int]
    ) -> xr.DataArray:
    in_raster = in_raster.where(
        in_raster.values != in_raster.rio.nodata,
        new_nodata,
        )
    in_raster = in_raster.rio.write_nodata(
        new_nodata,
        inplace=True,
        )
    return in_raster

# BACK-END FACING UTILITY FUNTIONS
def _intake_ambigous(
    in_data: Union[Raster, Shapefile],
    ) -> Union[xr.DataArray, gpd.GeoDataFrame]:
    """Somewhat less performant intake function when the input can be either a Raster or Shapefile"""
    if isinstance(in_data, os.PathLike):
        if in_data.suffix in RasterSuffixes:
            return load_raster(in_data)
        elif in_data.suffix in ShapefileSuffixes:
            return load_shapefile(in_data)
    elif isinstance(in_data, xr.DataArray) or isinstance(in_data, gpd.GeoDataFrame):
        return in_data

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
    Underlying function called in update_raster_values() to update a DataArray by x,y coordinates.
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

def _verify_shape_match(
    in_raster1: Raster,
    in_raster2: Raster,
    ) -> bool:
    # get dimension info
    shape1 = load_raster(in_raster1).shape
    shape2 = load_raster(in_raster2).shape
    len1 = len(shape1)
    len2 = len(shape2)

    # check that inputs have correct # of dimensions
    if max([len1, len2]) > 3 or min([len1, len2]) < 2:
        print('ERROR: A raster has incorrect dimensions. Must be f(x, y) or f(x, y, t).')
        raise TypeError

    # compare shapes appropriately
    if len1 == len2: return bool(shape1 == shape2)
    elif len1 > len2: return bool(shape1[1:] == shape2)
    else: return bool(shape1 == shape2[1:])

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
        name=index_name,
        )
    return xr.concat(
        objs=split_dict.values(),
        dim=index,
        )

def find_downstream_cell(
    d8_fdr: xr.DataArray,
    coords: Tuple[float, float],
    ) -> Tuple[float, float]:
    """
    Uses a D8 FDR to find the cell center coordinates downstream from any cell (specified
    Note: this replaces py:func:FindDownstreamCellTauDir(d, x, y, w) in the V1.1 repo.
    :param d8_fdr: (xr.DataArray or str raster path) a D8 Flow Direction Raster (dtype=Int).
    :param coords: (tuple) the input (lat:float, lon:float) to find the next cell downstream from.
    :returns: (tuple) an output (lat:float, lon:float) representing the cell center coorindates
        downstream from the cell defined via :param:coords.
    """
    # identify d8 fdr format
    d8_format = id_d8_format(d8_fdr)
    dir_dict = D8ConversionDicts[d8_format]
    dir_dict = dict(zip(dir_dict.values(), dir_dict.keys()))

    # get cell size
    cell_size = np.abs(d8_fdr.rio.resolution(recalc=True)[0])

    # get FDR cell value
    value = int(
        query_point(
            d8_fdr,
            coords,
            )
        )
    
    # find downstream cell coordinates via hashmap and return
    dxdy_dict = {
        'east': (cell_size, 0.0),
        'northeast': (cell_size, cell_size),
        'north': (0.0, cell_size),
        'northwest': (cell_size * -1.0, 0.0),
        'west': (cell_size * -1.0, 0.0),
        'southwest': (cell_size * -1.0, cell_size * -1.0),
        'south': (0.0, cell_size * -1.0),
        'southeast': (cell_size, cell_size * -1.0),
    }
    dx_dy_tuple = dxdy_dict[dir_dict[value]]

    return (coords[0] + dx_dy_tuple[0], coords[1] + dx_dy_tuple[1])

def _verify_coords_coverage(
    raster: xr.DataArray,
    coords: Tuple[float, float],
    ) -> bool:
    """Returns True if an x, y coordinate is in the bounds of a raster"""
    bbox = list(raster.rio.bounds())

    # check if x, y coordaintes are within bounds
    if coords[0] > bbox[0] and coords[0] < bbox[2]:
        if coords[1] > bbox[1] and coords[1] < bbox[3]: return True
    return False

def _verify_basin_coverage(
    raster: xr.DataArray,
    basin_shapefile: gpd.GeoDataFrame,
    ) -> bool:
    """
    Returns True if a basin shapefile/GeoDataFrame is completely covered by a raster.
    :param raster: (xr.DataArray) a georeferenced raster.
    :param basin_shapefile: (gpd.GeoDataFrame) basin shapefile.
    :returns: (boolean)
    """
    # reproject the raster to align with the basin_shapefile
    raster = reproject_raster(
        raster,
        basin_shapefile,
        )
    raster_bbox = np.array(raster.rio.bounds())
    shp_bbox = basin_shapefile.geometry.total_bounds
    
    # compare geometry to verify inclusion
    diff = np.array(raster_bbox) - np.array(shp_bbox)
    compare = np.sign(diff) == np.array([-1, -1, 1, 1])
    return np.all(compare)

def _verify_alignment(
    raster1: xr.DataArray,
    raster2: xr.DataArray,
    ) -> bool:
    """
    Returns True if the CRS, shape, and bbox of param:raster1 and param:raster2 match.
    Note: This only works for two 2D rasters!
    """
    raster_list = [raster1, raster2]
    for i, raster in enumerate(raster_list):
        if len(raster.shape) == 3:
            raster_list[i] = raster[1,:]

    if raster1.rio.crs == raster2.rio.crs and raster_list[0].shape == raster_list[1].shape:
        diff = np.array(raster_list[0].rio.bounds()) - \
            np.array(raster_list[1].rio.bounds())
        if np.max(diff) == 0: return True
    return False
        

