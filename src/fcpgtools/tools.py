from typing import Union, Dict, List, Tuple, Optional
import warnings
from pathlib import Path
import xarray as xr
import rioxarray as rio
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.enums import Resampling
import fcpgtools.utilities as utilities
from fcpgtools.terrainengine import protocols, engine_validator
from fcpgtools.custom_types import (
    Raster,
    RasterSuffixes,
    Shapefile,
    ShapefileSuffixes,
    D8ConversionDicts,
)
from fcpgtools.custom_types import PourPointLocationsDict, PourPointValuesDict


def load_raster(
    in_raster: Raster,
) -> xr.DataArray:
    """Loads a raster into a xarray.DataArray object."""
    if isinstance(in_raster, xr.DataArray):
        return utilities._format_nodata(in_raster.squeeze())
    if isinstance(in_raster, str) or in_raster is None:
        in_raster = Path(in_raster)
        if not in_raster.exists():
            raise FileNotFoundError(f'Input path {in_raster} is not found.')
    if not isinstance(in_raster, Path):
        raise TypeError(
            f'param:in_raster must be of type {Raster}!'
        )
    if in_raster.suffix == '.tif':
        return utilities._format_nodata(rio.open_rasterio(in_raster).squeeze())
    else:
        raise ValueError(
            f'{in_raster.suffix} is not a supported raster type. '
            f'Please choose from {RasterSuffixes}.'
        )


def load_shapefile(
    in_shapefile: Shapefile,
) -> gpd.GeoDataFrame:
    """Loads a shapefile into a geopandas.GeoDataFrame"""
    if isinstance(in_shapefile, gpd.GeoDataFrame):
        return in_shapefile
    if isinstance(in_shapefile, str):
        in_shapefile = Path(in_shapefile)
        if not in_shapefile.exists():
            raise FileNotFoundError(f'Input path {in_shapefile} is not found.')
    if not isinstance(in_shapefile, Path):
        raise TypeError(
            f'param:in_shapefile must be of type {Shapefile}!'
        )
    if in_shapefile.suffix == '.shp':
        return gpd.read_file(in_shapefile)
    else:
        raise ValueError(
            f'{in_shapefile.suffix} is not a supported shapefile type. '
            f'Please choose from {ShapefileSuffixes}.'
        )


def save_raster(
    out_raster: xr.DataArray,
    out_path: Union[str, Path],
) -> None:
    """Saves an xarray.DataArray to a .tif raster file at location param:out_path"""
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        warnings.warn(
            message=f'Cannot overwrite {out_path}! Saving raster failed.',
            category=UserWarning,
        )
        return None

    try:
        if out_path.suffix == '.tif':
            out_raster.rio.to_raster(out_path)
        else:
            raise ValueError(
                f'{out_raster.suffix} is not a supported raster output file type. '
                f'Please choose from {RasterSuffixes}.'
            )
    except Exception as e:
        warnings.warn(
            message=f'Could not save shapefile due to {e}',
            category=UserWarning,
        )


def save_shapefile(
    out_shapefile: gpd.GeoDataFrame,
    out_path: Union[str, Path]
) -> None:
    """Saves an geopandas.GeoDataFrame to a .shp file at location param:out_path"""
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        warnings.warn(
            message=f'Cannot overwrite {out_path}! Saving shapefile failed.',
            category=UserWarning,
        )
        return None

    try:
        if out_path.suffix == '.shp':
            out_shapefile.to_file(out_path)
        else:
            raise ValueError(
                f'{out_path.suffix} is not a supported output shapefile type. '
                f'Please choose from {ShapefileSuffixes}.'
            )
    except Exception as e:
        warnings.warn(
            message=f'Could not save shapefile due to {e}',
            category=UserWarning,
        )


def align_raster(
    in_raster: Raster,
    match_raster: Raster,
    resample_method: str = 'nearest',
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Aligns the projection/CRS, spatial extent, and resolution of one raster to another.

    Args:
        in_raster: Input raster that needs to be aligned.
        match_raster: Raster to align to.
        resample_method: A valid resampling method from rasterio.enums.Resample (default='nearest').
            NOTE: Do not use any averaging resample methods when working with a categorical raster!
        out_path: Defines a path to save the output raster.

    Returns:
        The output aligned raster.
    """
    in_raster = load_raster(in_raster)

    out_raster = in_raster.rio.reproject_match(
        match_raster,
        resampling=getattr(Resampling, resample_method),
    )

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def clip(
    in_raster: Raster,
    match_raster: Optional[Raster] = None,
    match_shapefile: Optional[Shapefile] = None,
    custom_bbox: Optional[List] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Clips a raster to the rectangular extent (aka bounding box) of another raster (or shapefile).

    Args:
        in_raster: Input raster.
        match_raster: If defined, in_raster is clipped to match the extent of match_raster.
        match_shapefile: A shapefile that is used to define the output extent if match_raster == None.
        out_path: Defines a path to save the output raster.
        custom_bbox: A list with bounding box coordinates that define the output extent if match_raster == None.
            Note: Coordinates must be of the form [minX, minY, maxX, maxY].
            Note: Using this parameter assumes that coordinates match the CRS of param:in_raster.

    Returns:
        The input raster clipped by the desired geometry.
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
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def reproject_raster(
    in_raster: Raster,
    out_crs: Optional[Union[Raster, Shapefile]] = None,
    resolution: Optional[Union[float, Tuple[float, float]]] = None,
    wkt_string: Optional[str] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Reprojects a raster to match another shapefile/raster's Coordinate Reference System (CRS), or a custom CRS.

    Args:
        in_raster: Input raster.
        out_crs: A raster or shapefile with the desired CRS to reproject to.
        resolution: Allows the output resolution to be overridden.
        wkt_string: Allows the user to define the output CRS using a custom valid WKT string.
        out_path: Defines a path to save the output raster.

    Returns:
        The input raster reprojected to match the desired Coordinate Reference System (CRS).
    """
    in_raster = load_raster(in_raster)
    if out_crs is not None:
        out_crs = utilities._get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
        resolution = None
    else:
        raise ValueError(
            'Must pass in either param:out_crs or param:wkt_string')

    out_raster = in_raster.rio.reproject(
        out_crs,
        resolution=resolution,
        nodata=in_raster.rio.nodata,
        kwargs={'dst_nodata': in_raster.rio.nodata},
    )

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def reproject_shapefile(
    in_shapefile: Shapefile,
    out_crs: Optional[Union[Raster, Shapefile]] = None,
    wkt_string: Optional[str] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Reprojects a shapefile to match another shapefile/raster's Coordinate Reference System (CRS), or a custom CRS.

    Args:
        in_shapefile: Input shapefile/GeoDataFrame.
        out_crs: A raster or shapefile with the desired CRS to reproject to.
        wkt_string: Allows the user to define the output CRS using a custom valid WKT string.
        out_path: Defines a path to save the output shapefile.

    Returns:
        The input shapefile reprojected to match the desired Coordinate Reference System (CRS).
    """
    in_shapefile = load_raster(in_shapefile)
    if out_crs is not None:
        out_crs = utilities._get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
    else:
        raise ValueError(
            'Must pass in either param:out_crs or param:wkt_string')

    out_shapefile = in_shapefile.to_crs(out_crs)
    if out_path is not None:
        save_shapefile(
            out_shapefile,
            out_path,
        )
    return out_shapefile


def resample(
    in_raster: Raster,
    match_raster: Raster,
    method: str = 'nearest',
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Resamples a raster to match another raster's cell size.

    Args:
        in_raster: Input raster.
        match_raster: A raster to match the resolution / cell size of.
        method: A valid resampling method from rasterio.enums.Resample.
            NOTE: Do not use any averaging resample methods when working with a categorical raster! 
        out_path: Defines a path to save the output raster.

    Returns:
        The input raster resampled to the desired resolution / cell size.
    """
    in_raster = load_raster(in_raster)
    match_raster = load_raster(match_raster)

    try:
        out_raster = in_raster.rio.reproject(
            in_raster.rio.crs,
            shape=(match_raster.rio.height, match_raster.rio.width),
            resampling=getattr(Resampling, method),
            kwargs={'dst_nodata': in_raster.rio.nodata},
        )

    except AttributeError:
        real_methods = vars(Resampling)['_member_names_']
        raise ValueError(
            f'Resampling method {method} is invalid! Please select from {real_methods}')

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def convert_fdr_formats(
    d8_fdr: Raster,
    out_format: str,
    in_format: Optional[str] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Converts the D8 encoding of Flow Direction Rasters (FDR).

    Args:
        d8_fdr: The input D8 Flow Direction Raster (FDR).
        out_format: A valid D8 flow direction format name in custom_types.D8ConversionDicts.keys().
        in_format:  A valid D8 flow direction format name in custom_types.D8ConversionDicts.keys() that
            overrides the auto-recognized format from param:d8_fdr.
            Note: manually inputting param:in_format will improve performance.
        out_path:  Defines a path to save the output raster.

    Returns:
        The re-encoded D8 Flow Direction Raster (FDR).
    """
    # identify the input D8 format
    d8_fdr = load_raster(d8_fdr)
    out_format = out_format.lower()
    if in_format is not None:
        in_format = in_format.lower()
    else:
        in_format = utilities._id_d8_format(d8_fdr)

    # check that both formats are valid before proceeding
    d8_formats = list(D8ConversionDicts.keys())
    if in_format not in d8_formats:
        raise TypeError(
            f'param:in_format = {in_format} which is not in {d8_formats}'
        )

    if out_format not in d8_formats:
        raise TypeError(
            f'param:out_format = {out_format} which is not in {d8_formats}'
        )

    # remove unexpected d8 values
    d8_fdr = utilities._remove_unexpected_d8_values(
        d8_fdr,
        in_format,
    )

    if in_format == out_format:
        return d8_fdr

    # get the conversion dictionary mapping
    mapping = dict(
        zip(
            D8ConversionDicts[in_format].values(),
            D8ConversionDicts[out_format].values(),
        )
    )

    # get values in pandas (no clean implementation in xarray)
    in_df = pd.DataFrame()
    out_df = pd.DataFrame()
    in_df[0] = d8_fdr.values.ravel()

    # apply the mapping and convert back to xarray
    out_df[0] = in_df[0].map(mapping)

    d8_fdr = d8_fdr.copy(
        data=out_df[0].values.reshape(d8_fdr.shape),
    )

    # update nodata
    d8_fdr.rio.write_nodata(
        D8ConversionDicts[out_format]['nodata'],
        inplace=True,
    )
    d8_fdr = d8_fdr.astype('int')

    if out_path is not None:
        save_raster(
            d8_fdr,
            out_path,
        )

    return d8_fdr


def make_fac_weights(
    parameter_raster: Raster,
    fdr_raster: Raster,
    out_of_bounds_value: Union[float, int],
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Preps param:parameter_raster for parameter accumulation by matching the nodata boundary to param:fdr_raster. 

    NOTE: Only this function AFTER aligning the parameter raster to the FDR raster via tools.align_raster()!

    Args: 
        parameter_raster: A parameter raster.
        fdr_raster: A Flow Direction Raster (either D8 or D-inf).
        out_of_bounds_value: The value to give param:parameter_raster cells outside the data
            boundary of param:fdr_raster. Note that this is automatically set within terrain_engine functions.
        out_path:  defines a path to save the output raster.

    Returns:
        The prepped parameter grid.
    """
    # intake rasters
    parameter_raster = load_raster(parameter_raster)
    fdr_raster = load_raster(fdr_raster)

    # check that shapes match
    if not utilities._verify_shape_match(fdr_raster, parameter_raster):
        raise TypeError(
            'The D8 FDR raster and the parameter raster must have the same shape. '
            'Please run fcpgtools.tools.align_raster(d8_fdr, parameter_raster).'
        )

    # use a where query to replace out of bounds values
    og_nodata = parameter_raster.rio.nodata
    og_crs = utilities._get_crs(parameter_raster)

    if not utilities._verify_alignment(parameter_raster, fdr_raster):
        raise TypeError(
            'param:parameter_raster and param:fdr_raster are not aligned! '
            'Please use tools.align_raster() before applying this tool!'
        )

    parameter_raster = parameter_raster.where(
        fdr_raster.values != fdr_raster.rio.nodata,
        out_of_bounds_value,
    )

    # convert in-bounds nodata to 0
    if np.isin(og_nodata, parameter_raster.values):
        parameter_raster = parameter_raster.where(
            (fdr_raster.values == fdr_raster.rio.nodata) &
            (parameter_raster.values != og_nodata),
            0,
        )

    # update nodata and crs
    parameter_raster.rio.write_nodata(
        og_nodata,
        inplace=True,
    )

    parameter_raster.rio.write_crs(og_crs, inplace=True)
    parameter_raster = utilities._change_nodata_value(
        parameter_raster,
        out_of_bounds_value,
    )

    # save raster if necessary
    if out_path is not None:
        save_raster(
            parameter_raster,
            out_path,
        )

    return parameter_raster


def adjust_parameter_raster(
    parameter_raster: Raster,
    d8_fdr: Raster,
    upstream_pour_points: PourPointValuesDict,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Adds values to a parameter raster's at specific coordinates / pour points.

    The main utility of this function is to enable cascading accumulation values
    from one basin or raster to another via accumulate_parameter().

    Args:
        parameter_raster: Input parameter raster to update.
        d8_fdr: a D8 Flow Direction Raster.
        upstream_pour_points: A dictionary with coordinates to update values at,
            and the values to add.
        out_path: Defines a path to save the output raster.

    Returns:
        The updated parameter raster.
    """
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
        ds_coords = utilities._find_downstream_cell(
            d8_fdr,
            coords,
        )

        # verify coverage
        if not utilities._verify_coords_coverage(parameter_raster, ds_coords):
            warnings.warn(
                message=(
                    f'Cell downstream from pour point coords={coords} '
                    f'is out of bounds -> skipped!'
                ),
                category=UserWarning
            )
            continue

        if len(parameter_raster.shape) == 2:
            parameter_raster = utilities._update_raster_values(
                in_raster=parameter_raster,
                update_points=[(ds_coords, values_list[0])],
            )
        else:
            dim_index_values = parameter_raster[parameter_raster.dims[0]].values
            for band_index, _value in enumerate(dim_index_values):
                parameter_raster[band_index, :, :] = utilities._update_raster_values(
                    in_raster=parameter_raster[band_index, :, :],
                    update_points=[(ds_coords, values_list[band_index])],
                )

    if out_path is not None:
        save_raster(
            parameter_raster,
            out_path,
        )

    return parameter_raster


def make_decay_raster(
    distance_to_stream_raster: Raster,
    decay_factor: Union[int, float],
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Creates a decay raster based on distance to stream.

    This function is used to prep for decay_accumulate().
    Grid cell values are computed as the inverse number of grid cells,
    :code:`np.exp((-1 * distance_to_stream * cell_size) / (cell_size ** k))`,
    where k is a constant applied to the cell size values.

    Args:
        distance_to_stream_raster: A distance to stream raster output from 
            distance_to_stream().
        decay_factor: Dimensionless constant applied to decay factor denominator.
            NOTE: Set k to 2 for 'moderate' decay; greater than 2 for slower 
            decay; or less than 2 for faster decay.
        out_path: Defines a path to save the output raster.

    Returns:
        The output decay raster for use in decay_accumulate().
    """
    distance_to_stream_raster = load_raster(
        distance_to_stream_raster).astype('float')
    cell_size = distance_to_stream_raster.rio.resolution()[0]

    decay_array = np.exp(
        (-1 * distance_to_stream_raster.values *
         cell_size) / (cell_size ** decay_factor)
    )

    decay_raster = xr.DataArray(
        data=decay_array,
        coords=distance_to_stream_raster.coords,
        attrs=distance_to_stream_raster.attrs,
    )

    decay_raster.name = 'decay_raster'

    # save if necessary
    if out_path is not None:
        save_raster(
            decay_raster,
            out_path,
        )

    return decay_raster


def spatial_mask(
    in_raster: Raster,
    mask_shp: Union[gpd.GeoDataFrame, str],
    inverse: bool = False,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Applies a spatial mask via a shapefile to a raster.

    Primarily for masking rasters (i.e., FAC) by basin shapefiles, converting 
    out-of-mask raster values to NoData. A cell value can also be used to 
    create a mask for integer rasters. 
    NOTE: default behavior (inverse=False) will make it so cells NOT COVERED 
    by mask_shp -> NoData.

    Args:
        in_raster: Input raster.
        mask_shp: Shapefile used for masking.
        inverse: If True, cells that ARE COVERED by mask_shp -> NoData.
        out_path: Defines a path to save the output raster.

    Returns:
        The output spatially masked raster.
    """
    in_raster = load_raster(in_raster)
    mask_shp = load_shapefile(mask_shp)

    out_raster = in_raster.rio.clip(
        mask_shp.geometry.values,
        mask_shp.crs,
        all_touched=True,
        drop=False,
        invert=inverse,
    )

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def value_mask(
    in_raster: Raster,
    thresh: Optional[Union[int, float]] = None,
    greater_than: bool = True,
    equals: Optional[int] = None,
    inverse_equals: bool = False,
    in_mask_value: Optional[int] = None,
    out_mask_value: Optional[int] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """"Mask a raster via a value threshold.

    Primary use case is to identify high accumulation zones / stream cells.
    Cells included in the mask are given a value of 1, all other cells are given a value of 0 (unless out_mask_value!=None).
    NOTE: this function generalizes V1:pyfunc:makeStreams() functionality.

    Args:
        in_raster: Input raster.
        thresh:  The threshold to apply the value mask with.
        greater_than: If False, only values less than param:thresh are included in the mask.
        equals:  Only cells matching the value of param:equals are included in the mask.
        inverse_equals: Is True and param:equals==True, values NOT equal to :param:thresh are masked out.
        in_mask_value: Allows included cells to be given a non-zero integer value.
        out_mask_value: Allows non-included cells to be given a non-zero integer value.
        out_path: Defines a path to save the output raster.

    Returns:
        The output raster with all masked out values == nodata or param:out_mask_value.
    """
    # handle nodata / out-of-mask values
    in_raster = load_raster(in_raster)
    if out_mask_value is None:
        out_mask_value = in_raster.rio.nodata

    # build conditionals
    if equals and 'float' in str(in_raster.dtype):
        warnings.warn(
            message=(
                f'Applying an equality mask to a {in_raster.dtype} raster. '
                f'This is ill-advised!'
            ),
            category=UserWarning,
        )

    if equals and not inverse_equals:
        conditional = (in_raster == thresh)
    if equals and inverse_equals:
        conditional = (in_raster != thresh)
    elif greater_than:
        conditional = (in_raster > thresh)
    elif not greater_than:
        conditional = (in_raster < thresh)

    # set dtype
    if in_mask_value and out_mask_value is not None:
        dtype = 'int64'
    else:
        dtype = in_raster.dtype

    out_raster = in_raster.where(
        conditional,
        out_mask_value,
    )

    if in_mask_value is not None:
        out_raster = out_raster.where(
            (out_raster.values == out_mask_value),
            in_mask_value,
        )

    out_raster = out_raster.astype(dtype)
    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def mask_streams(
    fac_raster: Raster,
    accumulation_threshold: Union[int, float],
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """A simplified version of tools.value_mask() that outputs np.nan for non-'stream' cells below the accumulation threshold.

    Args:
        fac_raster: A single band flow accumulation (FAC) raster.
        accumulation_threshold: The flow accumulation threshold.

    Returns:
        The output raster with cells below the threshold encoded as np.nan
    """
    fac_raster = load_raster(fac_raster).astype('float')

    # handle input nodata
    fac_raster = fac_raster.where(
        (fac_raster != fac_raster.rio.nodata),
        np.nan,
    )

    # apply stream mask
    mask_streams = fac_raster.where(
        (fac_raster >= accumulation_threshold),
        np.nan,
    )
    mask_streams = mask_streams.rio.write_nodata(np.nan)

    # save if necessary
    if out_path is not None:
        save_raster(
            mask_streams,
            out_path,
        )

    return mask_streams


def binarize_nodata(
    in_raster: Raster,
    nodata_value: Optional[Union[float, int]] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Creates an output binary raster based on an input where nodata values -> 1, and valued cells -> 0.

    Note: while param:inverse=True this can be used with pyfunc:apply_mask() to match nodata cells between rasters.

    Args:
        in_raster: Input raster.
        nodata_value: If the nodata value for param:in_raster is not in the metadata,
            set this parameter to equal the cell value storing nodata (i.e., np.nan or -999).
        out_path: Defines a path to save the output raster.

    Returns:
        The output binary mask raster.
    """
    # handle nodata / out-of-mask values
    in_raster = load_raster(in_raster)
    if nodata_value is None:
        nodata_value = in_raster.rio.nodata

    # convert all values to 0 or 1
    nodata_binary = 1
    out_raster = in_raster.where(
        in_raster.isnull(),
        0,
    ).astype(in_raster.dtype)

    out_raster = out_raster.where(
        out_raster == 0,
        1,
    ).astype('uint8')

    out_raster.rio.write_nodata(
        nodata_binary,
        inplace=True,
    )

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def binarize_categorical_raster(
    cat_raster: Raster,
    categories_dict: Optional[Dict[int, str]] = None,
    ignore_categories: Optional[List] = None,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Converts a single band categorical raster into a binary multi-band binary raster.

    Each output band represent a unique category, where 1 encodes cells 
    belonging the the category, and 0 encodes cells belonging to any other category. 
    This function is used to prep a categorical raster for parameter_accumulate().

    Args:
        cat_raster: A categorical (dtype=int) raster with N unique categories 
            (i.e., land cover classes).
        categories_dict: A dictionary assigning string names (values) to 
            integer raster values (keys).
        ignore_categories: Category cell values not include in the output raster.
        out_path: Defines a path to save the output raster.

    Returns:
        A N-band multi-dimensional raster as a xarray DataArray object.
    """
    cat_raster = load_raster(cat_raster)
    cat_dtype = str(cat_raster.dtype)
    if not categories_dict:
        categories_dict = {}

    if 'int' not in cat_dtype:
        raise TypeError('Categorical rasters must be dtype=int.')
    if len(cat_raster.shape) >= 3:
        raise TypeError('Categorical rasters must be of form f(x, y).')

    categories = [int(i) for i in list(np.unique(cat_raster.values))]
    if not ignore_categories:
        ignore_categories = []

    combine_dict = {}
    count = 0
    for cat in categories:
        if cat in ignore_categories:
            continue
        if cat in list(categories_dict.keys()):
            index = categories_dict[cat]
        else:
            index = cat

        out_layer = cat_raster.where(
            cat_raster == cat,
            0,
        ).astype(cat_dtype)

        out_layer = out_layer.where(
            out_layer == 0,
            1,
        ).astype('uint8')

        combine_dict[(count, index)] = out_layer
        count += 1

    out_raster = utilities._combine_split_bands(combine_dict)

    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )
    return out_raster


def d8_to_dinfinity(
    d8_fdr: Raster,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Converts a D8 Flow Direction Raster to D-Infinity.

    Args:
        d8_fdr: A D8 Flow Direction Raster (dtype=int).
        out_path: Defines a path to save the output raster.

    Returns:
        The output D-Inf Flow Direction Raster.
    """

    # if not taudem format, convert
    d8_fdr = load_raster(d8_fdr)
    d8_fdr = convert_fdr_formats(
        d8_fdr,
        out_format='taudem',
    )

    # replace nodata with nan and convert to float
    dinf_fdr = d8_fdr.where(
        (d8_fdr.values != d8_fdr.rio.nodata),
        np.nan,
    ).astype('float32')

    dinf_fdr.rio.write_nodata(
        np.nan,
        inplace=True,
    )

    # convert to d-infinity / radians (as floats, range 0 - 6.2)
    dinf_fdr = ((dinf_fdr - 1) * np.pi) / 4
    dinf_fdr.name = 'DInfinity_FDR'

    # save if necessary
    if out_path is not None:
        save_raster(
            dinf_fdr,
            out_path,
        )

    return dinf_fdr


def find_basin_pour_points(
    fac_raster: Raster,
    basins_shp: str,
    basin_id_field: str = 'HUC12',
    use_huc4: bool = True,
) -> PourPointLocationsDict:
    """Find pour points (aka outflow cells) in a FAC raster by basin using a shapefile.

    Args:
        fac_raster: A Flow Accumulation Cell raster (FAC).
        basins_shp: A .shp shapefile containing basin geometries.
        basin_id_field: Default behavior is for each GeoDataFrame row to be a unique basin.
            However, if one wants to use a higher level basin id that is shared across rows,
            this should be set to the column header storing the higher level basin id.
        use_huc4: Either 'HUC4' or 'HUC12'.

    Returns:
        A dictionary with keys (i.e., basin IDs) storing coordinates as a tuple(x, y).
    """
    fac_raster = load_raster(fac_raster)
    basins_shp = load_shapefile(basins_shp).to_crs(fac_raster.rio.crs)

    # verify that we can find the basin_id_field
    if basin_id_field is not None:
        if basin_id_field not in list(basins_shp.columns):
            raise ValueError(
                f'param:basin_id_field = {basin_id_field} is not in param:basins_shp'
            )

    # convert basin levels if necessary PourPointLocationsDict
    pour_point_locations_dict = {}
    pour_point_locations_dict['pour_point_ids'] = []
    pour_point_locations_dict['pour_point_coords'] = []

    if use_huc4 and basin_id_field == 'HUC12':
        basins_shp['HUC4'] = basins_shp[basin_id_field].str[:4]
        sub_basin_id = 'HUC4'
    else:
        sub_basin_id = basin_id_field

    # iterate over sub basins and fill the
    basins_shp = basins_shp.dissolve(by=sub_basin_id).reset_index()

    for basin in basins_shp[sub_basin_id].unique():
        sub_shp = basins_shp.loc[basins_shp[sub_basin_id] == basin]

        # check extents of shapefile bbox and make sure all overlap the FAC raster extent
        if not utilities._verify_basin_coverage(fac_raster, sub_shp):
            warnings.warn(
                message=(
                    f'Sub basin with {sub_basin_id} == {basin} is not'
                    ' completely enclosed by param:raster! Some relevant areas may be missing.'
                ),
                category=UserWarning,
            )

        # apply spatial mask and find max accumulation value
        sub_raster = spatial_mask(
            fac_raster,
            sub_shp,
        )
        pour_point_locations_dict['pour_point_ids'].append(basin)
        pour_point_locations_dict['pour_point_coords'].append(
            utilities._get_max_cell(sub_raster))

    return pour_point_locations_dict


def find_fac_pour_point(
    fac_raster: Raster,
    basin_name: Optional[Union[str, int]] = None,
) -> PourPointLocationsDict:
    """Find pour points (aka outflow cells) in a FAC raster by basin using a shapefile.

    Args:
        fac_raster: A Flow Accumulation Cell raster (FAC).
        basin_name: Allows a name to be given to the FAC.

    Returns:
        A dictionary with keys (i.e., basin IDs) storing coordinates as a tuple(x, y).
    """
    # create a basic PourPointLocationsDict for the full fac_raster
    fac_raster = load_raster(fac_raster)
    pour_point_locations_dict = {}

    if not basin_name:
        basin_name = 0
    pour_point_locations_dict['pour_point_ids'] = [basin_name]
    pour_point_locations_dict['pour_point_coords'] = [
        utilities._get_max_cell(fac_raster)]

    return pour_point_locations_dict


def get_pour_point_values(
    pour_points_dict: PourPointLocationsDict,
    accumulation_raster: Raster,
) -> PourPointValuesDict:
    """Get the accumulation raster values from downstream pour points.

    NOTE: This function is intended to feed into accumulate_flow() or 
    parameter_accumulate() param:upstream_pour_points.

    Args:
        pour_points_dict: A dictionary of form custom_types.PourPointValuesDict.
        accumulation_raster: A Flow Accumulation Cell raster (FAC) or a 
            parameter accumulation raster.

    Returns:
        A list of tuples (one for each pour point) storing their coordinates [0]
            and accumulation value [1].
    """
    # pull in the accumulation raster
    accumulation_raster = load_raster(accumulation_raster)

    # remove old values if accidentally passed in
    if 'pour_point_values' in list(pour_points_dict.keys()):
        del pour_points_dict['pour_point_values']

    # split bands if necessary
    if len(accumulation_raster.shape) > 2:
        raster_bands = utilities._split_bands(accumulation_raster)
    else:
        raster_bands = {(0, 0): accumulation_raster}

    # iterate over all basins and bands, extract values
    dict_values_list = []
    for pour_point_coords in pour_points_dict['pour_point_coords']:
        basin_values_list = []
        for band in raster_bands.values():
            basin_values_list.append(
                utilities._query_point(
                    band,
                    pour_point_coords,
                )[-1]
            )
        dict_values_list.append(basin_values_list)

    # convert to custom_types.PourPointValuesDict and return
    pour_points_dict['pour_point_values'] = dict_values_list
    return pour_points_dict


def make_fcpg(
    param_accum_raster: Raster,
    fac_raster: Raster,
    out_path: Optional[Union[str, Path]] = None,
) -> xr.DataArray:
    """Creates a Flow Conditioned Parameter Grid raster by dividing a parameter accumulation raster by a Flow Accumulation Cell (FAC) raster.

    Args:
        param_accum_raster: (xr.DataArray or str raster path)
        fac_raster: (xr.DataArray or str raster path) input FAC raster.
        out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.

    Returns:
        The output FCPG raster as a xarray DataArray object.
    """
    # bring in data
    fac_raster = load_raster(fac_raster)
    param_accum_raster = load_raster(param_accum_raster)

    fcpg_raster = param_accum_raster / (fac_raster + 1)
    fcpg_raster.name = 'FCPG'

    # save if necessary
    if out_path is not None:
        save_raster(
            fcpg_raster,
            out_path,
        )

    return fcpg_raster


def check_function_kwargs(
    function: callable,
    engine: str,
) -> Dict[str, Union[str, int, float]]:
    """Provides a dictionary of allowed kwargs keywords + input types for a function.

    NOTE: This function will raise a ValueError if a non-terrain_engine
        function is provided as the input.

    Args:
        function: A function belonging to a terrain_engine class.
        engine: The name of the engine being used.

    Returns:
        A dictionary with allowed kwargs as keys, and allowed input types as values.
    """

    engine = engine.lower()
    if engine not in engine_validator.NameToTerrainEngineDict.keys():
        raise ValueError(
            f'engine:{engine} is not a valid engine! Please choose from '
            f'{list(engine_validator.NameToTerrainEngineDict.keys())}'
        )
    else:
        engine_class = engine_validator.NameToTerrainEngineDict[engine]
        kwargs_dict = engine_class.function_kwargs

    if function.__name__ not in kwargs_dict.keys():
        raise ValueError(
            f'Function:{function.__name__} does not take kwargs or is not '
            f'valid for terrain_engine={engine}!'
        )
    else:
        return kwargs_dict[function.__name__]


@engine_validator.validate_engine(protocols.SupportsAccumulateFlow)
def accumulate_flow(
    d8_fdr: Raster,
    engine: protocols.SupportsAccumulateFlow = 'pysheds',
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    weights: Optional[xr.DataArray] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Create a Flow Accumulation Cell (FAC) raster from a D8 Flow Direction Raster.

    Args:
        d8_fdr: A  D8 Flow Direction Raster (dtype=Int).
        engine: A terrain engine class that supports flow accumulation.
        upstream_pour_points: A list of lists each with with coordinate tuples 
            as the first item [0], and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as 
            upstream basin pour points.
        weights: A grid defining the value to accumulate from each cell. 
            Default is a grid of 1s.
        out_path: Defines a path to save the output raster.
        **kwargs: keyword arguments, specific options depend on the engine being used.

    Returns:
        The output Flow Accumulation Cells (FAC) raster.
    """
    # reformat param:d8_fdr if necessary
    d8_fdr = utilities._match_d8_format(d8_fdr, engine)

    # execute function w/ the chosen engine
    return engine.accumulate_flow(
        d8_fdr,
        upstream_pour_points=upstream_pour_points,
        weights=weights,
        out_path=out_path,
        **kwargs,
    )


@engine_validator.validate_engine(protocols.SupportsAccumulateParameter)
def accumulate_parameter(
    d8_fdr: Raster,
    parameter_raster: Raster,
    engine: protocols.SupportsAccumulateParameter = 'pysheds',
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Create a parameter accumulation raster from a D8 FDR and a parameter raster.

    A key aspect of this function is that the output DataArray will have 
    dimensions matching param:parameter_raster.

    Args:
        d8_fdr: A D8 Flow Direction Raster (dtype=Int).
        parameter_raster: A parameter raster aligned via tools.align_raster()
            with the us_fdr. This can be multi-dimensional (i.e. f(x, y, t)), 
            and if so, a multi-dimensional output is returned.
        engine: A terrain engine class that supports parameter accumulation.
        upstream_pour_points: A list of lists each with with coordinate tuples 
            as the first item [0], and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as 
            upstream basin pour points.
        out_path: Defines a path to save the output raster.
        **kwargs: keyword arguments, specific options depend on the engine being used.

    Returns:
        The output parameter accumulation raster.
    """
    # reformat param:d8_fdr if necessary
    d8_fdr = utilities._match_d8_format(d8_fdr, engine)

    # execute function w/ the chosen engine
    return engine.accumulate_parameter(
        d8_fdr,
        parameter_raster,
        upstream_pour_points=upstream_pour_points,
        out_path=out_path,
        **kwargs,
    )


@engine_validator.validate_engine(protocols.SupportsExtremeUpslopeValues)
def extreme_upslope_values(
    d8_fdr: Raster,
    parameter_raster: Raster,
    engine: protocols.SupportsExtremeUpslopeValues = 'taudem',
    mask_streams: Optional[Raster] = None,
    out_path: Optional[Union[str, Path]] = None,
    get_min_upslope: bool = False,
    **kwargs,
) -> xr.DataArray:
    """Finds the max(default)/min value of a parameter grid upstream from each cell.

    NOTE: Replaces tools.ExtremeUpslopeValue() from V1 FCPGtools. 

    Args:
        d8_fdr: A flow direction raster .
        parameter_raster: A parameter raster to find the max values from.
        engine: A terrain engine class that supports finding extreme upslope values.
        mask_streams: A stream mask raster from tools.mask_streams().
            If provided, the output will be masked to only stream cells.
        out_path: Defines a path to save the output raster.
        get_min_upslope: If True, the minimum upslope value is assigned to each cell.
        **kwargs: keyword arguments, specific options depend on the engine being used.

    Returns:
        A raster with max (or min) upstream value of the parameter grid as each cell's value.
    """
    # reformat param:d8_fdr if necessary
    d8_fdr = utilities._match_d8_format(d8_fdr, engine)

    # execute function w/ the chosen engine
    return engine.extreme_upslope_values(
        d8_fdr,
        parameter_raster,
        mask_streams=mask_streams,
        out_path=out_path,
        get_min_upslope=get_min_upslope,
        **kwargs,
    )


@engine_validator.validate_engine(protocols.SupportsDistanceToStream)
def distance_to_stream(
    d8_fdr: Raster,
    fac_raster: Raster,
    accum_threshold: int,
    engine: protocols.SupportsDistanceToStream = 'taudem',
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Calculates cell distances from accumulation threshold defined streams.

    NOTE: Replaces tools.dist2stream() from V1 FCPGtools.

    Args:
        d8_fdr: A D8 Flow Direction Raster (dtype=Int).
        fac_raster: A Flow Accumulation Cell (FAC) raster output from accumulate_flow().
        accum_threshold: The # of upstream/accumulated cells to consider a cell a stream.
        engine: A terrain engine class that supports calculating distance to stream.
        out_path: Defines a path to save the output raster.
        **kwargs: keyword arguments, specific options depend on the engine being used.

    Returns:
        A raster with values of D8 flow distance from each cell to the nearest stream.
    """
    # reformat param:d8_fdr if necessary
    d8_fdr = utilities._match_d8_format(d8_fdr, engine)

    # execute function w/ the chosen engine
    return engine.distance_to_stream(
        d8_fdr,
        fac_raster,
        accum_threshold,
        out_path=out_path,
        **kwargs,
    )


@engine_validator.validate_engine(protocols.SupportsDecayAccumulation)
def decay_accumulation(
    d8_fdr: Raster,
    decay_raster: Raster,
    engine: protocols.SupportsDecayAccumulation = 'taudem',
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    parameter_raster: Optional[Raster] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Creates a "decayed" D-Infinity based accumulation raster via a decay raster.

    NOTE: Replaces tools.decayAccum() from V1 FCPGtools. This can be used
    to accumulate a parameter or just cells counts.

    Args:
        dinf_fdr: A flow direction raster in D-Infinity format. 
            This input can be made with d8_to_dinfinity().
        decay_raster: A decay 'multiplier' raster calculated from distance 
            to stream via make_decay_raster().
        engine: A terrain engine class that supports decayed accumulation.
        upstream_pour_points: A list of lists each with with coordinate tuples 
            as the first item [0], and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as 
            upstream basin pour points.
        parameter_raster: A parameter raster aligned via align_raster() with the us_fdr. 
            This can be multi-dimensional (i.e. f(x, y, t)), and if so, 
            a multi-dimensional output is returned.
        out_path: Defines a path to save the output raster.
        **kwargs: keyword arguments, specific options depend on the engine being used.

    Returns:
        The output decayed accumulation raster.
    """
    # reformat param:d8_fdr if necessary
    d8_fdr = utilities._match_d8_format(d8_fdr, engine)

    # execute function w/ the chosen engine
    return engine.decay_accumulation(
        d8_fdr,
        decay_raster,
        upstream_pour_points=upstream_pour_points,
        parameter_raster=parameter_raster,
        out_path=out_path,
        **kwargs,
    )
