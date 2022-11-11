from typing import Union, Tuple, Dict, List
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from fcpgtools.types import Raster, FDRD8Formats, D8ConversionDicts, PourPointLocationsDict, PourPointValuesDict
from fcpgtools.utilities import intake_raster, clip, reproject_raster, \
    resample, id_d8_format

# CLIENT FACING FUNCTIONS
def align_raster(
    in_raster,
    match_raster: Raster,
    resample_method: str = 'bilinear', 
    out_path: str = None,
    ) -> xr.DataArray:

    out_raster = clip(
        in_raster,
        match_raster,
        )
    out_raster = reproject_raster(
        in_raster,
        out_crs=match_raster,
        )
    out_raster = resample(
        in_raster,
        match_raster,
        method=resample_method,
        out_path=out_path,
        )
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
    print(f'Converted the D8 Flow Direction Raster (FDR) from {in_format} format'
    f' to {out_format}')
    return d8_fdr
    

def find_cell_downstream(
    d8_fdr: Raster,
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
    # get index of cell and index and use to query surrounding cells
    raise NotImplementedError

# raster masking function
def spatial_mask(
    in_raster: Raster,
    mask_shp: Union[gpd.GeoDataFrame, str] = None,
    out_path: str = None,
    mask_cell_value: int = None,
    inverse: bool = False,
    ) -> xr.DataArray:
    """
    Primarily for masking rasters (i.e., FAC) by basin shapefiles, converting out-of-mask raster
    values to NoData. A cell value can also be used to create a mask for integer rasters. 
    Note: default behavior (inverse=False) will make it so cells NOT COVERED by mask_shp -> NoData.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param mask_shp: (geopandas.GeoDataFrame or a str shapefile path) shapefile used for masking.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param mask_cell_value: (int, optional) if mask_shp == None this parameter can be used to mask
        cells (i.e., change to NoData) if they equal mask_cell_value.
    :param inverse: (bool, default=False) if True, cells that ARE COVERED by mask_shp -> NoData.
    :returns: (xr.DataArray) the output binary mask raster.
    """
    raise NotImplementedError

def value_mask(
    in_raster: Raster,
    thresh: Union[int,float] = None,
    greater_than: bool = True,
    equals: int = None,
    out_mask_value: int = None,
    out_path: str = None,
    inverse: bool = False,
    ) -> xr.DataArray:
    """"
    Mask a raster via a value threshold. Primary use case is to identify high acumulation zones / stream cells.
    Cells included in the mask are given a value of 1, all other cells are given a value of 0 (unless out_mask_value!=None).
    Note: this function generalizes V1:pyfunc:makeStreams() functionality.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param thresh: (int or float, default=None) 
    :param greater_than: (bool, default=True) if False, only values less than param:thresh are included in the mask.
    :param equals: (int, default=None) if not None, only cells matching the value of param:equals are included in the mask.
    :param out_mask_value: (int, default=None) allows non-included cells to be given a non-zero integer value.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param inverse: (bool, default=False) if True, the inverse of the mask is made.
    :returns: (xr.DataArray) the output binary mask raster.
    """
    raise NotImplementedError

def nodata_mask(
    in_raster: Raster, 
    inverse: bool = False,
    nodata_value: Union[float,int] = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Creates an output binary raster based on an input where nodata values -> 1, and valued cells -> 0.
    Note: while param:inverse=True this can be used with pyfunc:apply_mask() to match nodata cells between rasters.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param inverse: (bool, default=False) if True, values that are NOT nodata -> 1, and nodata values -> 0.
    :param nodata_value: (float->np.nan or int) if the nodata value for param:in_raster is not in the metadata,
        set this parameter to equal the cell value storing nodata (i.e., np.nan or -999).
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the output binary mask raster.
    """
    raise NotImplementedError

def apply_mask(
    in_raster: Raster, 
    mask_raster: Raster, 
    inverse: bool = False, 
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Converts all values NOT included within a mask (i.e., value=0 while inverse=False) param:in_raster's nodata value.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param mask_raster: (xr.DataArray or str raster path) a binary "mask" raster where value=0 -> nodata in param:in_raster.
    :param inverse: (bool, default=False) if True param:mask_raster cells with a value of 1 are converted to nodata.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) the output raster with nodata cells.
    """
    raise NotImplementedError

def binarize_categorical_rasters(
    cat_raster: Raster, 
    ignore_caregories: list = None,
    out_path: str = None,
    split_rasters: bool = False,
    ) -> xr.DataArray:
    """
    :param cat_raster: (xr.DataArray or str raster path) a categorical (dtype=int) raster with N
        unique categories (i.e., land cover classes).
    :param ignore_categories: (list of integers, default=None) category cell values not include
        in the output raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param split_rasters: (bool, default=False) if True AND out_path != None, the directory
        in out_path is used to store N separate .tif files for each unique cat_raster value.
        Note that this is the behavior in V1.1 of FCPGTools.
    :returns: (xr.DataArray) a N-band multi-dimensional raster as a xarray DataArray object.
    """
    raise NotImplementedError

def find_pour_points(
    fac_raster: Raster, 
    basins_shp: str = None, 
    basin_id_field: str = None,
    ) -> PourPointLocationsDict:
    """
    Find pour points (aka outflow cells) in a FAC raster by basin using a shapefile.
    :param fac_raster: (xr.DataArray or str raster path) a Flow Accumulation Cell raster (FAC).
    :param basins_shp: (str path) a .shp shapefile containing basin geometries.
    :basin_id_field: default behavior is for each GeoDataFrame row to be a unique basin.s
        However, if one wants to use a higher level basin id that is shared acrcoss rows,
        this should be set to the column header storing the higher level basin id.
    :returns: (dict) a dictionary with keys (i.e., basin IDs) storing coordinates as a tuple(lat, lon).
    """
    # check extents of shapefile bbox and make sure all overlap the FAC raster extent
    raise NotImplementedError

def get_pour_point_values(
    pour_point_locations: PourPointLocationsDict,
    accumulation_raster: Raster,
    ) -> PourPointValuesDict:
    """
    Get the accumlation raster values from downstream pour points. Note: This function is intended to feed
        into terrainengine.fac_from_fdr() or terrainengine.parameter_accumlate() param:upstream_pour_points.
    :param pour_point_locations:  (dict) a dictionary with keys (i.e., basin IDs) storing coordinates as a tuple(lat, lon).
    :param accumulation_raster: (xr.DataArray or str raster path) a Flow Accumulation Cell raster (FAC) or a
        parameter accumulation raster.
    :returns: (list) a list of tuples (one for each pour point) storing their coordinates [0] and accumulation value [1].
    """
    # to support multi-dimensionality I think it is best to iterate over this function as the pour point locations will be constant.
    #TODO: let's actually keep it as a basinID references dictionary, storing either a list of tuples (one for each band), or just a tuple
    raise NotImplementedError
    
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
    raise NotImplementedError

#TODO: Evaluate feasibility of implementing 
#These are extra add ons that would be nice to implement budget permitting 
#Prepare flow direction raster (FDR)
def fix_pits(
    dem: Raster,
    out_path: str = None,
    fix: bool = True,
    ) -> xr.DataArray:
    """
    Detect and fills single cell "pits" in a DEM raster using pysheds: .detect_pits()/.fill_pits().
    :param dem: (xr.DataArray or str raster path) the input DEM raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param fix: (bool, default=True) if False, a print statement warns of the # of single cell pits
        without fixing them. The input raster is returned as is.
    :returns: (xr.DataArray) the filled DEM an xarray DataArray object (while fix=True).
    """
    raise NotImplementedError

def fix_depressions(
    dem: Raster,
    out_path: str = None,
    fix: bool = True,
    ) -> xr.DataArray:
    """
    Detect and fills multi-cell "depressions" in a DEM raster using pysheds: .detect_depressions()/.fill_depressions().
    :param dem: (xr.DataArray or str raster path) the input DEM raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param fix: (bool, default=True) if False, a print statement warns of the # of dpressions
        without fixing them. The input raster is returned as is.
    :returns: (xr.DataArray) the filled DEM an xarray DataArray object (while fix=True).
    """
    raise NotImplementedError

def fix_flats(
    dem: Raster,
    out_path: str = None,
    fix: bool = True,
    ) -> xr.DataArray:
    """
    Detect and resolves "flats" in a DEM using pysheds: .detect_flats()/.resolve_flats().
    :param dem: (xr.DataArray or str raster path) the input DEM raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param fix: (bool, default=True) if False, a print statement warns of the # flats
        without fixing them. The input raster is returned as is.
    :returns: (xr.DataArray) the resolved DEM an xarray DataArray object (while fix=True).
    """
    raise NotImplementedError

def d8_fdr(
    dem: Raster,
    out_path: str = None,
    out_format: str = 'TauDEM',
    ) -> xr.DataArray:
    """
    Creates a flow direction raster from a DEM. Can either save the raster or keep in memory.
    :param dem: (xr.DataArray or str raster path) the DEM from which to make the FDR.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param out_format: (str, default=TauDEM) type of D8 flow direction encoding for output.
    :returns: the FDR as a xarray DataArray object.
    """
    raise NotImplementedError

def batch_process(
    dataset: xr.Dataset,
    function: callable = None,
    out_path: str = None,
    *kwargs: dict,
    ) -> xr.Dataset:
    """
    Applies a function to each DataArray in a Dataset (should this be built into the functions themselves??)
    :param Dataset: (xr.Dataset) an xarray Dataset where all DataArrays are ready to be processed together.
    :param function: (callable) a function to apply to the Dataset.
    :param out_path: (str path, default=None) a zarr or netcdf extension path to save the Dataset.
    :param **kwargs: (dict) allows for non-default keyword parameters for param:function to be specified.
    :returns: (xr.Dataset) the output Dataset with each DataArray altered by param:function.
    """
    raise NotImplementedError


