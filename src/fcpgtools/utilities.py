from typing import Union
import os
from pathlib import Path
import xarray as xr
import rioxarray as rio
import geopandas as gpd
from geoengine.protocols import Raster, Shapefile
from geoengine.protocols import RasterSuffixes, ShapefileSuffixes

# functions used across other utility functions
def _intake_raster(in_raster: Raster) -> xr.DataArray:
    """Used in the first line of most functions to make sure all inputs are DataArray"""
    if isinstance(in_raster, xr.DataArray):
        return in_raster
    elif isinstance(in_raster, os.PathLike):
        return rio.open_rasterio(in_raster)

def _intake_shapefile(in_shapefile: Shapefile) -> gpd.GeoDataFrame:
    """Used in the first line of most functions to make sure all shapefile data is in a GeoDataFrame"""
    if isinstance(in_shapefile, gpd.GeoDataFrame):
        return in_shapefile
    elif isinstance(in_shapefile, os.PathLike):
        return gpd.read_file(in_shapefile)

def _intake_ambigous(in_data: Union[Raster, Shapefile]) -> Union[xr.DataArray, gpd.GeoDataFrame]:
    """Somewhat less performant intake function when the input can be either a Raster or Shapefile"""
    if isinstance(in_data, os.PathLike):
        if in_data.suffix in RasterSuffixes:
            return _intake_raster(in_data)
        elif in_data.suffix in ShapefileSuffixes:
            return _intake_shapefile(in_data)
    elif isinstance(in_data, Union[xr.DataArray, gpd.GeoDataFrame]):
        return in_data

def _get_crs(out_crs: Union[Raster, Shapefile]) -> str:
    crs_data = _intake_ambigous(out_crs)

    if isinstance(crs_data, xr.DataArray):
        return crs_data.rio.crs.to_wkt()
    elif isinstance(crs_data, gpd.GeoDataFrame):
        return crs_data.crs.to_wkt()

def _save_raster(out_raster: xr.DataArray,
                out_path: Union[str, os.PathLike]) -> None:
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        print(f'WARNING: Cannot overwrite {out_path}!')
        return None
    try:
        out_raster.rio.to_raster(out_path)
    except Exception as e:
        print(e)

def _save_shapefile(out_shapefile: gpd.GeoDataFrame,
                    out_path: Union[str, os.PathLike]) -> None:
    if isinstance(out_path, str):
        out_path = Path(out_path)

    if Path.exists(out_path):
        print(f'WARNING: Cannot overwrite {out_path}!')
        return None
    try:
        out_shapefile.to_file(out_path)
    except Exception as e:
        print(e)

# core utility functions
def clip(in_raster: Raster,
         match_raster: Raster,
         out_path: str = None,
         custom_shp: Shapefile = None,
         custom_bbox: list = None,
         ) -> xr.DataArray:
    """
    Clips a raster to the rectangular extent (aka bounding box) of another raster (or shapefile).
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param match_raster: (xr.DataArray or str raster path) if defined, in_raster is
        clipped to match the extent of match_raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param custom_shp: (str path or GeoDataFame, default=None) a shapefile that is used to define
        the output extent if match_raster == None.
    :param custom_bbox: (list, default=None) a list with bounding box coordinates that define the output
        extent if match_raster == None. Coordinates must be of the form [minX, minY, maxX, maxY].
    :returns: (xr.DataArray) the clipped raster as a xarray DataArray object.
    """
    in_raster = _intake_raster(in_raster)

    ## FUNTION HERE
    out_raster = None # CHANGE THIS
    if out_path is not None:
        _save_raster(out_raster, out_path)

def reproject_raster(in_raster: Raster,
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
    in_raster = _intake_raster(in_raster)
    if out_crs is not None:
        out_crs = _get_crs(out_crs)
    elif wkt_string is not None:
        out_crs = wkt_string
    else:
        #TODO: Update exceptions
        print('Must pass in eitehr param:out_crs or param:wkt_string')
        return None

    out_raster = in_raster.rio.reproject(out_crs, nodata=in_raster.rio.nodata)
    if out_path is not None:
        _save_raster(out_raster, out_path)
    return out_raster


def reproject_shapefile(in_shapefile: Shapefile,
                        out_crs: Union[Raster, Shapefile] = None,
                        wkt_string: str = None,
                        out_path: str = None,
                        ) -> xr.DataArray:
    in_shapefile = _intake_raster(in_shapefile)
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
        _save_shapefile(out_shapefile, out_path)
    return out_shapefile

def resample(in_raster: Raster,
             match_raster: Raster,
             out_path: str = None,
             custom_cell_size: Union[float, int] = None,
             ) -> xr.DataArray:
    """
    Resamples a raster to match another raster's cell size, or a custom cell size.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param match_raster: (xr.DataArray or str raster path) if defined, in_raster is
        resampled to match the cell size of match_raster.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param custom_cell_size: (float or int) custom cell size, only used if match_raster == None.
    :returns: (xr.DataArray) the resampled raster as a xarray DataArray object.
    """
    in_raster = intake_raster(in_raster)

    ## FUNTION HERE
    out_raster = None # CHANGE THIS
    if out_path is not None:
        save_raster(out_raster, out_path)

def batch_process(Dataset: xr.Dataset,
                  function: callable = None,
                  out_path: str = None,
                  **kwargs: dict,
                  ) -> xr.Dataset:
    """
    Applies a function to each DataArray in a Dataset (should this be built into the functions themselves??)
    :param Dataset: (xr.Dataset) an xarray Dataset where all DataArrays are ready to be processed together.
    :param function: (callable) a function to apply to the Dataset.
    :param out_path: (str path, default=None) a zarr or netcdf extension path to save the Dataset.
    :param **kwargs: (dict) allows for non-default keyword parameters for param:function to be specified.
    :returns: (xr.Dataset) the output Dataset with each DataArray altered by param:function.
    """
    pass


def sample_raster(raster: xr.DataArray,
                  coords: tuple,
                  ) -> Union[float, int]:
    """
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :param coords: (tuple) coordinate as (lat:float, lon:float) of the cell to be sampled.
    :returns: (float or int) the cell value at param:coords.
    """
    pass


def get_min_cell(raster: xr.DataArray) -> list[tuple, Union[float, int]]:
    """
    Get the minimum cell coordinates + value from a raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (list) a list (len=2) with the min cell's coordinate tuple [0] and value [1]
        i.e., [coords:tuple, value:Union[float, int]].
    """
    pass


def get_max_cell(raster: xr.DataArray) -> list[tuple, Union[float, int]]:
    """
    Get the maximum cell coordinates + value from a raster.
    :param raster: (xr.DataArray) a raster as a DataArray in memory.
    :returns: (list) a list (len=2) with the max cell's coordinate tuple [0] and value [1]
        i.e., [coords:tuple, value:Union[float, int, np.array]].
    """
    pass


def update_cell_values(in_raster: Union[xr.DataArray, str],
                       coords: tuple, value: Union[float, int],
                       out_path: str = None,
                       ) -> xr.DataArray:
    """
    Update a specific raster cell's value based on it's coordindates. This is primarily used
    to add upstream accumulation values as boundary conditions before making a FAC or FCPG.
    :param in_raster: (xr.DataArray or str raster path) input raster.
    :param coords: (tuple) coordinate as (lat:float, lon:float) of the cell to be updated.
    :param value: (float or int) new value to give the cell.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :returns: param:in_raster with the updated cell value as a xarray DataArray object.
    """
    pass


def change_nodata(in_raster: Union[xr.DataArray, str],
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
    pass


def change_dtype(in_raster: Union[xr.DataArray, str],
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
    pass


def get_raster_bbox(raster: xr.DataArray) -> list:
    """
    Get bounding box coordinates of a raster.
    :param raster: (xr.DataArray or str raster path) a georeferenced raster.
    :returns: (list) list with bounding bbox coordinates - [minX, minY, maxX, maxY]
    """
    # this function is used to in verify_extent() as well as clip().
    pass


def verify_extent(raster: xr.DataArray,
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
    pass


def minimize_extent(in_raster: Union[xr.DataArray, str],
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
    pass


def get_shp_bbox(shp: Union[str, gpd.GeoDataFrame]) -> list:
    """
    Get bbox coordinates of a shapefile.
    :param shp: (geopandas.GeoDataFrame or str shapefile path) a georeferenced shapefile.
    :returns: (list) list with bounding bbox coordinates - [minX, minY, maxX, maxY]
    """
    pass
