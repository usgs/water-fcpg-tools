import xarray as xr
from typing import Union
from fcpgtools.custom_types import Raster


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
    # NOTE: likely not needed!
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
    # NOTE: likely not needed!
    raise NotImplementedError


# TODO: Evaluate feasibility of implementing
# These are extra add ons that would be nice to implement budget permitting
# Prepare flow direction raster (FDR)
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
