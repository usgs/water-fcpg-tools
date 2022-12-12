from pathlib import Path
from typing import Union, List, Tuple, Dict, TypedDict
from xarray import DataArray
from geopandas import GeoDataFrame
from numpy import ndarray
from pysheds.grid import Grid
from pysheds.view import Raster as PyShedsRaster


Raster = Union[DataArray, str, Path]
Shapefile = Union[GeoDataFrame, str, Path]
Engines = ('taudem', 'pysheds')
RasterSuffixes = ('.tif')
ShapefileSuffixes = ('.shp')
FDRD8Formats = ('esri', 'taudem')

# create D8 conversion dictionaries
D8ConversionDicts = {
    'taudem': {
        'southeast': 8,
        'south': 7,
        'southwest': 6,
        'west': 5,
        'northwest': 4,
        'north': 3,
        'northeast': 2,
        'east': 1,
        'nodata': 0,
    },
    'esri': {
        'southeast': 2,
        'south': 4,
        'southwest': 8,
        'west': 16,
        'northwest': 32,
        'north': 64,
        'northeast': 128,
        'east': 1,
        'nodata': 255,
    }
}

# create a custom type hint dictionary for pour points


class PourPointLocationsDict(TypedDict):
    pour_point_ids: List[Union[int, str]]

    # (x, y) in raster coordinates
    pour_point_coords: List[Tuple[float, float]]


class PourPointValuesDict(PourPointLocationsDict):
    # the lists in the list will be len==1 if a one band array is supplied
    pour_point_values: List[List[Union[float, int]]]

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


class Taudemdistance_to_streamInputDict(TypedDict):
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
                   Taudemdistance_to_streamInputDict,
                   TaudemMaxUpslopeInputDict, ]
