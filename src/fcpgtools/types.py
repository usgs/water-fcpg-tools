from typing import Union, List, Tuple, Dict, TypedDict
from xarray import DataArray
from geopandas import GeoDataFrame
from numpy import ndarray
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster

#TODO: We'll want to replace the `str` type here with some type of path object
Raster = Union[DataArray, str]
Shapefile = Union[GeoDataFrame, str]
Engines = Tuple[str('taudem'), str('pysheds')]
# RasterSuffixes = Tuple[str('.tif')]
# ShapefileSuffixes = Tuple[str('.shp')]

# create custom type hint for PyShedsInputDict
class PyShedsInputDict(TypedDict):
    input_array: ndarray
    raster: PyShedsRaster
    grid: Grid

# create classess to add to TauDEMDict:Union[TypeDict,...]
class TaudemFACInputDict(TypedDict):
    fdr: str
    outFl: str
    cores: int
    mpiCall: str
    mpiArg: str

class TaudemDist2StreamInputDict(TypedDict):
    fdr: str
    fac: str
    outRast: str
    thresh: int
    cores: int
    mpiCall: str
    mpiArg: str

class TaudemMaxUpslopeInputDict(TypedDict):
    fdr: str
    param: str
    outRast: str
    accum_type: str
    cores: int
    mpiCall: str
    mpiArg: str

TauDEMDict = Union[TaudemFACInputDict,
    TaudemDist2StreamInputDict,
    TaudemMaxUpslopeInputDict,]