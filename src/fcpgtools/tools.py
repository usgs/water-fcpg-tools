from typing import Union, Tuple, Dict, List
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.enums import Resampling
from fcpgtools.types import Raster, FDRD8Formats, D8ConversionDicts, PourPointLocationsDict, PourPointValuesDict
from fcpgtools.utilities import intake_raster, intake_shapefile, save_raster, clip, reproject_raster, \
    resample, id_d8_format, _combine_split_bands, _verify_basin_coverage, get_max_cell, sample_raster, \
    _split_bands, _verify_shape_match, _get_crs, _replace_nodata_value, _verify_alignment

# CLIENT FACING FUNCTIONS
def align_raster(
    in_raster,
    match_raster: Raster,
    resample_method: str = 'nearest', 
    out_path: str = None,
    ) -> xr.DataArray:

    out_raster = in_raster.rio.reproject_match(
        match_raster,
        resampling=getattr(Resampling, resample_method),
        )
    
    if out_path is not None:
        save_raster(out_raster, out_path)
    return out_raster

def convert_fdr_formats(
    d8_fdr: Raster,
    out_format: str,
    in_format: str = None,
    ) -> xr.DataArray:
    """
    Converts the D8 encoding of Flow Direction Rasters (FDR).
    :param d8_fdr: (xr.DataArray, or path) the input D8 Flow Direction Raster (FDR).
    :param out_format: (str)
    :param in_format: (str, optional -> ESRI or TauDEM) a string D8 name that
        overrides the auto-recognized format from param:d8_fdr.
        Note: manually inputting param:in_format will improve performance.
    :returns: (xr.DataArray) the re-encoded D8 Flow Direction Raster (FDR).
    """
    # identify the input D8 format
    d8_fdr = intake_raster(d8_fdr)
    out_format = out_format.lower()
    if in_format is not None: in_format = in_format.lower()
    else:
        in_format = id_d8_format(d8_fdr)
    
    # check that both formats are valid before proceeding
    if in_format not in FDRD8Formats: return print(
        f'ERROR: param:in_format = {in_format} which is not in {FDRD8Formats}'
        )
    if out_format not in FDRD8Formats: return print(
        f'ERROR: param:out_format = {out_format} which is not in {FDRD8Formats}'
        )
    if in_format == out_format: return d8_fdr

    # get the conversion dictionary
    in_dict, out_dict = D8ConversionDicts[in_format], D8ConversionDicts[out_format]

    # convert appropriately using pandas (no clean implementation in xarray)
    #TODO: Improve this somewhat, works for now but we can likely test simpler solutions
    #NOTE: One option is using df.map() to covert all format values at once rather than iteratively
    for key, old_value in in_dict.items():
        if old_value in list(np.unique(d8_fdr.values)):
            new_value = out_dict[key]
            if old_value != new_value:
                df = pd.DataFrame()
                df[0] = d8_fdr.values.ravel()
                df[0].replace(
                    old_value,
                    new_value,
                    inplace=True,
                    )
                d8_fdr = d8_fdr.copy(
                    data=df[0].values.reshape(d8_fdr.shape),
                    )

    # update nodata
    d8_fdr.rio.write_nodata(out_dict['nodata'], inplace=True)

    print(f'Converted the D8 Flow Direction Raster (FDR) from {in_format} format'
    f' to {out_format}')
    return d8_fdr

def prep_parameter_grid(
    parameter_raster: xr.DataArray,
    fdr_raster: xr.DataArray,
    out_of_bounds_value: Union[float, int],
    ) -> xr.DataArray:

    # check that shapes match
    if not _verify_shape_match(fdr_raster, parameter_raster):
        print('ERROR: The D8 FDR raster and the parameter raster must have the same shape. '
        'Please run fcpgtools.tools.align_raster(d8_fdr, parameter_raster).')
        raise TypeError

    # use a where query to replace out of bounds values
    og_nodata = parameter_raster.rio.nodata
    og_crs = _get_crs(parameter_raster)
    out_crs = _get_crs(fdr_raster)

    if not _verify_alignment(parameter_raster, fdr_raster):
        parameter_raster = align_raster(
            parameter_raster,
            fdr_raster,
            resample_method='nearest',
            )

    parameter_raster = parameter_raster.where(
        fdr_raster.values != fdr_raster.rio.nodata,
        out_of_bounds_value,
        )

    # convert in-bounds nodata to 0
    if np.isin(og_nodata, parameter_raster.values):
        parameter_raster = parameter_raster.where(
            (fdr_raster.values == fdr_raster.rio.nodata) & \
                (parameter_raster.values != og_nodata),
            0,
            )

    # update nodata and crs
    parameter_raster.rio.write_nodata(
        og_nodata,
        inplace=True,
        )
    parameter_raster.rio.write_crs(og_crs, inplace=True)
    parameter_raster = _replace_nodata_value(
        parameter_raster,
        out_of_bounds_value,
        )

    return parameter_raster

# raster masking function
def spatial_mask(
    in_raster: Raster,
    mask_shp: Union[gpd.GeoDataFrame, str],
    out_path: str = None,
    inverse: bool = False,
    ) -> xr.DataArray:
    """
    Primarily for masking rasters (i.e., FAC) by basin shapefiles, converting out-of-mask raster
    values to NoData. A cell value can also be used to create a mask for integer rasters. 
    Note: default behavior (inverse=False) will make it so cells NOT COVERED by mask_shp -> NoData.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param mask_shp: (geopandas.GeoDataFrame or a str shapefile path) shapefile used for masking.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param inverse: (bool, default=False) if True, cells that ARE COVERED by mask_shp -> NoData.
    :returns: (xr.DataArray) the output spatially masked raster.
    """
    in_raster = intake_raster(in_raster)
    mask_shp = intake_shapefile(mask_shp)

    out_raster = in_raster.rio.clip(
        mask_shp.geometry.values,
        mask_shp.crs,
        drop=False,
        invert=inverse,
        )

    if out_path is not None:
        save_raster(out_raster, out_path)
    return out_raster

def value_mask(
    in_raster: Raster,
    thresh: Union[int, float] = None,
    greater_than: bool = True,
    equals: int = None,
    inverse_equals: bool = False,
    in_mask_value: int = None,
    out_mask_value: int = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """"
    Mask a raster via a value threshold. Primary use case is to identify high acumulation zones / stream cells.
    Cells included in the mask are given a value of 1, all other cells are given a value of 0 (unless out_mask_value!=None).
    Note: this function generalizes V1:pyfunc:makeStreams() functionality.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param thresh: (int or float, default=None) 
    :param greater_than: (bool, default=True) if False, only values less than param:thresh are included in the mask.
    :param equals: (int, default=None) if not None, only cells matching the value of param:equals are included in the mask.
    :param inverse_equals: (bool, default=False) is True and param:equals==True, values NOT equal to :param:thresh are masked out.
    :param in_mask_value: (int, default=None) allows included cells to be given a non-zero integer value.
    :param out_mask_value: (int, default=None) allows non-included cells to be given a non-zero integer value.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the output raster with all masked out values == nodata or param:out_mask_value.
    """
    # handle nodata / out-of-mask values
    in_raster = intake_raster(in_raster)
    if out_mask_value is None: out_mask_value = in_raster.rio.nodata
    
    # build conditionals
    if equals and 'float' in str(in_raster.dtype): print(
        f'WARNING: Applying an equality mask to a {in_raster.dtype} raster'
        )
    
    if equals and not inverse_equals: conditional = (in_raster == thresh)
    if equals and inverse_equals: conditional = (in_raster != thresh)
    elif greater_than: conditional = (in_raster > thresh)
    elif not greater_than: conditional = (in_raster < thresh)

    # set dtype
    if in_mask_value and out_mask_value is not None: dtype = 'int64'
    else: dtype = in_raster.dtype

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
        save_raster(out_raster, out_path)
    return out_raster

def binarize_nodata(
    in_raster: Raster,
    nodata_value: Union[float, int] = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Creates an output binary raster based on an input where nodata values -> 1, and valued cells -> 0.
    Note: while param:inverse=True this can be used with pyfunc:apply_mask() to match nodata cells between rasters.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param nodata_value: (float->np.nan or int) if the nodata value for param:in_raster is not in the metadata,
        set this parameter to equal the cell value storing nodata (i.e., np.nan or -999).
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the output binary mask raster.
    """
    # handle nodata / out-of-mask values
    in_raster = intake_raster(in_raster)
    if nodata_value is None: nodata_value = in_raster.rio.nodata

    # convert all values to 0 or 1
    nodata_binary = 1
    out_raster = in_raster.where(
        in_raster.isnull(),
        0,
        ).astype(
            in_raster.dtype,
            )
    out_raster = out_raster.where(
        out_raster == 0,
        1,
        ).astype('uint8')

    out_raster.rio.write_nodata(nodata_binary, inplace=True)

    if out_path is not None:
        save_raster(out_raster, out_path)
    return out_raster

def binarize_categorical_raster(
    cat_raster: Raster, 
    categories_dict: Dict[int, str] = {},
    ignore_categories: list = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    :param cat_raster: (xr.DataArray or str raster path) a categorical (dtype=int) raster with N
        unique categories (i.e., land cover classes).
    :param categogies_dict: (dict) a dictionary assigning string names (values) to integer raster values (keys).
    :param ignore_categories: (list of integers, default=None) category cell values not include
        in the output raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) a N-band multi-dimensional raster as a xarray DataArray object.
    """
    cat_raster = intake_raster(cat_raster)
    cat_dtype = str(cat_raster.dtype)
    if 'int'  not in cat_dtype:
        print('ERROR: Categorical rasters must be dtype=int.')
        return TypeError
    if len(cat_raster.shape) >= 3:
        print('ERROR: Categorical rasters must be of form f(x, y).')
        return TypeError

    categories = [int(i) for i in list(np.unique(cat_raster.values))]
    if not ignore_categories: ignore_categories = []

    combine_dict = {}
    count = 0
    for i, cat in enumerate(categories):
        if cat not in ignore_categories:
            if cat in list(categories_dict.keys()): index = categories_dict[cat]
            else: index = cat
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

    out_raster = _combine_split_bands(combine_dict)

    if out_path is not None:
        save_raster(out_raster, out_path)
    return out_raster

def d8_to_dinf(
    d8_fdr: Raster,
    ) -> xr.DataArray:
    """Converts a D8 Flow Direction Raster to D-Infinity"""

    # if not taudem format, convert
    d8_fdr = intake_raster(d8_fdr)
    d8_fdr = convert_fdr_formats(
        d8_fdr,
        out_format='taudem',
        )
    
    # replace nodata with nan and convert to float
    dinf_fdr = d8_fdr.where(
        (d8_fdr.values != d8_fdr.rio.nodata),
        np.nan,
        ).astype('float32')
    dinf_fdr.rio.write_nodata(np.nan, inplace=True)

    # convert to d-infinity / radians (as floats, range 0 - 6.2)
    dinf_fdr = ((dinf_fdr - 1) * np.pi) / 4
    dinf_fdr.name = 'DInfinity_FDR'
    return dinf_fdr

def find_pour_points(
    fac_raster: Raster, 
    basins_shp: str = None, 
    basin_id_field: str = 'HUC12',
    use_huc4: bool = True,
    ) -> PourPointLocationsDict:
    """
    Find pour points (aka outflow cells) in a FAC raster by basin using a shapefile.
    :param fac_raster: (xr.DataArray or str raster path) a Flow Accumulation Cell raster (FAC).
    :param basins_shp: (str path) a .shp shapefile containing basin geometries.
    :basin_id_field: default behavior is for each GeoDataFrame row to be a unique basin.s
        However, if one wants to use a higher level basin id that is shared acrcoss rows,
        this should be set to the column header storing the higher level basin id.
    :param basin_level: (str), either 'HUC4' or 'HUC12'
    :returns: (dict) a dictionary with keys (i.e., basin IDs) storing coordinates as a tuple(x, y).
    """
    fac_raster = intake_raster(fac_raster)
    basins_shp = intake_shapefile(basins_shp)

    # verify that we can find the basin_id_field
    if basin_id_field is not None:
        if basin_id_field not in list(basins_shp.columns):
            print(f'ERROR: param:basin_id_field = {basin_id_field} is not in param:basins_shp')
            return ValueError
    
    # convert basin levels if necessary PourPointLocationsDict
    pour_point_locations_dict = {}
    pour_point_locations_dict['pour_point_ids'] = []
    pour_point_locations_dict['pour_point_coords'] = []

    if use_huc4 and basin_id_field == 'HUC12':
        print('Using HUC4 level flow basins, converting from HUC12')
        basins_shp['HUC4'] = basins_shp[basin_id_field].str[:4]
        sub_basin_id = 'HUC4'
    else: sub_basin_id = basin_id_field
    
    # iterate over sub basins and fill the
    basins_shp = basins_shp.dissolve(by=sub_basin_id).reset_index()

    for basin in basins_shp[sub_basin_id].unique():
        sub_shp = basins_shp.loc[basins_shp[sub_basin_id] == basin]

        # check extents of shapefile bbox and make sure all overlap the FAC raster extent
        if not _verify_basin_coverage(fac_raster, sub_shp):
            print(f'WARNING: sub basin with {sub_basin_id} == {basin} is not'
            ' completely enclosed by param:raster! Some relevant areas may be missing.')
        
        # apply spatial mask and find max accumulation value
        sub_raster = spatial_mask(
            fac_raster,
            sub_shp,
            )
        pour_point_locations_dict['pour_point_ids'].append(basin)
        pour_point_locations_dict['pour_point_coords'].append(get_max_cell(sub_raster))
    
    return pour_point_locations_dict
    
def get_pour_point_values(
    pour_points_dict: PourPointLocationsDict,
    accumulation_raster: Raster,
    ) -> PourPointValuesDict:
    """
    Get the accumlation raster values from downstream pour points. Note: This function is intended to feed
        into terrainengine.fac_from_fdr() or terrainengine.parameter_accumlate() param:upstream_pour_points.
    :param pour_points_dict: (dict) a dictionary of form fcpgtools.types.PourPointValuesDict.
    :param accumulation_raster: (xr.DataArray or str raster path) a Flow Accumulation Cell raster (FAC) or a
        parameter accumulation raster.
    :returns: (list) a list of tuples (one for each pour point) storing their coordinates [0] and accumulation value [1].
    """
    # pull in the accumulation raster
    accumulation_raster = intake_raster(accumulation_raster)
    
    # remove old values if accidentally passed in
    if 'pour_point_values' in list(pour_points_dict.keys()):
        del pour_points_dict['pour_point_values']

    # split bands if necessary
    if len(accumulation_raster.shape) > 2:
        raster_bands = _split_bands(accumulation_raster)
    else:
        raster_bands = {(0, 0): accumulation_raster}

    # iterate over all basins and bands, extract values
    dict_values_list = []
    for pour_point_coords in pour_points_dict['pour_point_coords']:
        basin_values_list = []
        for band in raster_bands.values():
            basin_values_list.append(
                sample_raster(
                    band,
                    pour_point_coords,
                    )
                )
        dict_values_list.append(basin_values_list)

    # convert to types.PourPointValuesDict and return
    pour_points_dict['pour_point_values'] = dict_values_list
    return pour_points_dict

# make FCPG raster
def create_fcpg(
    param_accum_raster: Raster,
    fac_raster: Raster,
    ignore_nodata: bool = False,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Creates a Flow Conditioned Parameter Grid raster by dividing a paramater accumulation
    raster by a Flow Accumulation Cell (FAC) raster. FCPG = param_accum / fac.
    :param param_accum_raster: (xr.DataArray or str raster path)
    :param fac_raster: (xr.DataArray or str raster path) input FAC raster.
    :param ignore_nodata: (bool, default=False) by default param_accum_raster cells with nodata
        are kept as nodata. If True, the lack of parameter accumulation is ignores, and the FAC value
        if given to the cell without adjustment.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the output FCPG raster as a xarray DataArray object.
    """
    # bring in data
    fac_raster = intake_raster(fac_raster)
    param_accum_raster = intake_raster(param_accum_raster)

    #TODO: deal with zero values in a more clever way (upstream in the pipeline?)
    fcpg_raster = param_accum_raster / (fac_raster + 1)
    fcpg_raster.name = 'FCPG'

    # save if necessary
    if out_path is not None:
        save_raster(fcpg_raster, out_path)

    #TODO: deal with nodata, replace with raw FAC scores if ignore_nodata=True

    return fcpg_raster


