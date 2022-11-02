import xarray as xr
import geopandas as gpd
import pydaymet
from geoengine.protocols import Raster

# STORES REMOTE SERVER DATA RETRIEVAL PRODUCTS
# more for extendibility

def get_daymet_precipitation(fdr_raster: Raster, time_range: list, timescale: str = 'monthly') -> xr.DataArray:
    bbox = ''
    crs = ''
    # get bbox geodataframe and crs from input FDR

    dataset = pydaymet.get_bygeom(bbox, time_range, crs, variables='prcp', time_scale=timescale)

    # convert dataset into some sort of standardized datarray (no need to support to much flex)
    pass
