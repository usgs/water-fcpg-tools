import os
import warnings
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Union, List, Tuple, Dict
import fcpgtools.tools as tools
from fcpgtools.custom_types import (
    Raster, 
    Shapefile,
    RasterSuffixes, 
    ShapefileSuffixes,
    D8ConversionDicts,
)


def _id_d8_format(
    d8_fdr: Raster,
) -> str:
    """Identifies the D8 flow direction raster and returns one of the string keys in custom_types.D8ConversionDicts (i.e. 'taudem' or 'esri')"""
    d8_fdr = tools.load_raster(d8_fdr)
    uniques = np.unique(d8_fdr.values)
    if np.nanmax(uniques) > 8:
        return 'esri'
    elif np.nanmax(uniques) <= 8:
        return 'taudem'
    else:
        raise TypeError(
            'Cant recognize D8 Flow Direction Raster format '
            'as either ESRI or TauDEM. Please use the param:in_format for '
            'pyfunc:convert_fdr_formats()'
        )


def _match_d8_format(
    d8_fdr: Raster,
    engine: object,
) -> xr.DataArray:
    """Matches the D8 format to the appropriate terrain engine"""
    d8_format = _id_d8_format(d8_fdr)
    try:
        if d8_format != engine.d8_format:
            d8_fdr = tools.convert_fdr_formats(
                d8_fdr,
                out_format=engine.d8_format,
                in_format=d8_format,
            )
    except AttributeError:
        raise AttributeError(
            f'Terrain engine {engine.__name__} is missing attribute d8_format!')
    except KeyError:
        raise KeyError(
            f'd8_format: {d8_format} is missing from fcpgtools.custom_types.D8ConversionDicts.keys()!')
    except TypeError:
        warnings.warn(
            message=(
                f'Could not ID the D8 format automatically! '
                f'Please make sure its in {engine.d8_format} format '
                f'for param:engine={engine.__name__}.'    
            ),
            category=UserWarning,
        )
    return d8_fdr


def _update_raster_values(
    in_raster: Union[xr.DataArray, str],
    update_points: List[Tuple[Tuple[float, float], Union[float, int]]],
) -> xr.DataArray:
    """Update a specific raster cell's value based on it's coordinates.

    This is primarily used to add upstream accumulation values as boundary conditions before making a FAC or FCPG.

    Args:
        in_raster: Input raster.
        update_points: A list of tuples storing cell coordinates updated values
            of the form [((x_coord:float, y_coord:float), updated_value),...].

    Returns:
        The input raster with the updated cell value.
    """
    out_raster = tools.load_raster(in_raster)

    for update_tuple in update_points:
        if update_tuple[-1] != np.nan:
            _update_cell_value(
                out_raster,
                coords=update_tuple[0],
                value=update_tuple[-1],
            )

    return out_raster


def _query_point(
    raster: xr.DataArray,
    coords: Tuple[float, float],
) -> Tuple[Tuple[float, float], Union[float, int]]:
    """Retrieves a value from a f(x, y) raster at a given coordinate point.

    NOTE: If the coordinate is not in param:raster, the nearest value is returned!

    Args:
        raster: A raster as a DataArray in memory.
        coords: Coordinates as Tuple(lat:float, lon:float) of the cell to be sampled.

    Returns:long_lat_tuple
        The cell value at param:coords.
    """
    selection = raster.sel(
        {'x': coords[0], 'y': coords[1]},
        method='nearest',
    )
    return ((selection.x.item(0), selection.y.item(0)), selection.values.item(0))


def _get_min_cell(
    raster: xr.DataArray,
) -> Tuple[float, float]:
    """Get the minimum cell (x, y ) coordinates from a single band raster."""
    xmin_index = raster.argmin(dim=['x', 'y'])['x'].data.item(0)
    ymin_index = raster.argmin(dim=['x', 'y'])['y'].data.item(0)

    min_slice = raster.isel(
        {'x': xmin_index, 'y': ymin_index},
    )
    return (min_slice.x.values.item(0),
            min_slice.y.values.item(0))


def _get_max_cell(
    raster: xr.DataArray,
) -> Tuple[float, float]:
    """Get the maximum cell (x, y) coordinates from a single band raster."""
    xmax_index = raster.argmax(dim=['x', 'y'])['x'].data.item(0)
    ymax_index = raster.argmax(dim=['x', 'y'])['y'].data.item(0)

    max_slice = raster.isel(
        {'x': xmax_index, 'y': ymax_index},
    )
    return (max_slice.x.values.item(0),
            max_slice.y.values.item(0))


def _change_nodata_value(
    in_raster: xr.DataArray,
    new_nodata: Union[float, int],
) -> xr.DataArray:
    """Changes all nodata cells in a raster to a new value, then updates the raster's nodata encoding

    Args:
        in_raster: Input raster.
        new_nodata: A value to encode nodata as. Note that it should match the dtype of param:in_raster.

    Returns:
        The input raster with nodata values and encoding updated.
    """
    in_raster = in_raster.where(
        in_raster.values != in_raster.rio.nodata,
        new_nodata,
    )
    in_raster = in_raster.rio.write_nodata(
        new_nodata,
        inplace=True,
    )
    return in_raster


def _intake_ambiguous(
    in_data: Union[Raster, Shapefile],
) -> Union[xr.DataArray, gpd.GeoDataFrame]:
    """A somewhat less performant intake function when the input can be either a Raster or Shapefile"""
    if isinstance(in_data, os.PathLike):
        if in_data.suffix in RasterSuffixes:
            return tools.load_raster(in_data)
        elif in_data.suffix in ShapefileSuffixes:
            return tools.load_shapefile(in_data)
    elif isinstance(in_data, xr.DataArray) or isinstance(in_data, gpd.GeoDataFrame):
        return in_data


def _format_nodata(
    in_raster: xr.DataArray,
) -> xr.DataArray:
    """If in_raster.rio.nodata is None, a nodata value is added. For dtype=float -> np.nan, for dtype=int -> 255."""
    if in_raster.rio.nodata is None:
        og_dtype = str(in_raster.dtype)
        if 'float' in og_dtype:
            nodata_value = np.nan
        elif 'int' in og_dtype:
            nodata_value = 255
        if 'int8' in og_dtype:
            if np.min(np.unique(in_raster.values)) < 0:
                in_raster = in_raster.astype('int16')
            else:
                in_raster = in_raster.astype('uint8')

        in_raster.rio.write_nodata(
            nodata_value,
            inplace=True,
        )
    return in_raster


def _get_crs(
    out_crs: Union[Raster, Shapefile],
) -> str:
    """Gets the Coordinate Reference System of a raster or a shapefile as a WKT string."""
    crs_data = _intake_ambiguous(out_crs)

    if isinstance(crs_data, xr.DataArray):
        return crs_data.rio.crs.to_wkt()
    elif isinstance(crs_data, gpd.GeoDataFrame):
        return crs_data.crs.to_wkt()


def _verify_dtype(
    raster: xr.DataArray,
    value: Union[float, int],
) -> bool:
    """Verifies that a value fits the dtype of a raster."""
    dtype = str(raster.dtype)
    if 'float' in dtype:
        return True
    elif not isinstance(value, int):
        return False
    if 'int8' in dtype and value > 255:
        return False
    elif 'int16' in dtype and value > 32767:
        return False
    elif 'int32' in dtype and value > 2147483647:
        return False
    else:
        return True


def _update_cell_value(
    raster: xr.DataArray,
    coords: Tuple[float, float],
    value: Union[float, int],
) -> xr.DataArray:
    """Underlying function called in _update_raster_values() to update a DataArray by x,y coordinates.

    Args:
        raster: A raster as a DataArray in memory.
        coords: Coordinates as Tuple(lat:float, lon:float) of the cell to be updated.
        value: The new value to give the cell.

    Returns:
        The input raster with the updated cell value.
    """
    if _verify_dtype(raster, value):
        raster.loc[{'x': coords[0], 'y': coords[1]}] = value
        return raster
    else:
        raise TypeError(
            f'Value {value} does not match DataArray dtype = {raster.dtype}')


def _verify_shape_match(
    in_raster1: xr.DataArray,
    in_raster2: xr.DataArray,
) -> bool:
    """Verifies that the shape of two rasters match"""
    shape1 = in_raster1.shape
    shape2 = in_raster2.shape
    len1 = len(shape1)
    len2 = len(shape2)

    # check that inputs have correct # of dimensions
    if max([len1, len2]) > 3 or min([len1, len2]) < 2:
        raise TypeError(
            'A raster has incorrect dimensions. Must be f(x, y) or f(x, y, t).')

    # compare shapes appropriately
    if len1 == len2:
        return bool(shape1 == shape2)
    elif len1 > len2:
        return bool(shape1[1:] == shape2)
    else:
        return bool(shape1 == shape2[1:])


def _split_bands(
    in_raster: xr.DataArray,
) -> Dict[Tuple[int, Union[int, str, np.datetime64]], xr.DataArray]:
    """Splits a 3 dimensional xr.DataArray into 2D arrays indexed by either an int or string dimension label.

    Args:
        in_raster: A raster with a 3rd dimension (i.e. band, or f(x, y, t)).

    Returns:
        A dictionary with the int or string 3rd dimension label as keys, storing 2D data arrays.
    """
    if len(in_raster.shape) > 3:
        raise TypeError(f'param:in_raster (xr.DataArray) has 4 dimensions (shape={in_raster.shape}).'
                        ' Please use a 2 or 3 dimension xr.DataArray.')
    if len(in_raster.shape) < 3:
        print(
            'WARNING: param:in_raster was expected to have 3-dimensions, but only has two.')
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
    """Combines the output of _split_bands() back into a multi-dimensional xarray.DataArray"""
    index_name = 'band'
    if isinstance(
        list(split_dict.keys())[0][-1],
        np.datetime64,
    ):
        index_name = 'time'

    # re-create the 4th dimension index and concat
    index = pd.Index(
        [i[-1] for i in list(split_dict.keys())],
        name=index_name,
    )

    return xr.concat(
        objs=split_dict.values(),
        dim=index,
    )


def _find_downstream_cell(
    d8_fdr: xr.DataArray,
    coords: Tuple[float, float],
) -> Tuple[float, float]:
    """Uses a D8 FDR to find the cell center coordinates downstream from any cell.

    Note: this replaces py:func:FindDownstreamCellTauDir(d, x, y, w) in the V1.1 repo.

    Args:
        d8_fdr: A D8 Flow Direction Raster (dtype=Int).
        coords: The input (lat:float, lon:float) to find the next cell downstream from.

    Returns:
        An output (lat:float, lon:float) representing the cell center coordinates 
            downstream from the cell defined via :param:coords.
    """
    # identify d8 fdr format
    d8_format = _id_d8_format(d8_fdr)
    dir_dict = D8ConversionDicts[d8_format]
    dir_dict = dict(zip(dir_dict.values(), dir_dict.keys()))

    # get cell size
    cell_size = np.abs(d8_fdr.rio.resolution(recalc=True)[0])

    # get FDR cell value
    new_coords, value = _query_point(
        d8_fdr,
        coords,
    )
    value = int(value)

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

    return (new_coords[0] + dx_dy_tuple[0], new_coords[1] + dx_dy_tuple[1])


def _verify_coords_coverage(
    raster: xr.DataArray,
    coords: Tuple[float, float],
) -> bool:
    """Returns True if an x, y coordinate is in the bounds of a raster."""
    bbox = list(raster.rio.bounds())

    # check if x, y coordinates are within bounds
    if coords[0] > bbox[0] and coords[0] < bbox[2]:
        if coords[1] > bbox[1] and coords[1] < bbox[3]:
            return True
    return False


def _verify_basin_coverage(
    raster: xr.DataArray,
    basin_shapefile: gpd.GeoDataFrame,
) -> bool:
    """Returns True if a basin shapefile/GeoDataFrame is completely covered by a raster."""
    raster = tools.reproject_raster(
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
    """Returns True if the CRS, shape, and bbox of param:raster1 and param:raster2 match. Note that this only works for two f(x, y) rasters!"""
    raster_list = [raster1, raster2]
    for i, raster in enumerate(raster_list):
        if len(raster.shape) == 3:
            raster_list[i] = raster[1, :]

    if raster1.rio.crs == raster2.rio.crs and raster_list[0].shape == raster_list[1].shape:
        diff = np.array(raster_list[0].rio.bounds()) - \
            np.array(raster_list[1].rio.bounds())
        if np.max(diff) == 0:
            return True
    return False
