from pathlib import Path
from typing import Union, List, Tuple, TypedDict
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


class PourPointLocationsDict(TypedDict):
    """Custom type hint dict for storing basin pour point locations.

    Attributes: 
        pour_point_ids: A list of basin/region ids of length N.
        pour_point_coords: A list of (x, y) in raster coordinates of length N.
    """
    pour_point_ids: List[Union[int, str]]
    pour_point_coords: List[Tuple[float, float]]


class PourPointValuesDict(PourPointLocationsDict):
    """Custom type hint dict for storing pour point accumulation values.

    Attributes: 
        pour_point_values: A list of N lists, eaching storing values associated with the
            list's index location in PourPointLocationsDict['pour_point_ids'].
            The length of each list is equal to the # of bands in the accumulation raster.
    """
    pour_point_values: List[List[Union[float, int]]]


class PyShedsInputDict(TypedDict):
    input_array: ndarray
    raster: PyShedsRaster
    grid: Grid


class PyShedsFACkwargsDict(TypedDict):
    fdir: PyShedsRaster
    weights: PyShedsRaster
    dirmap: Tuple[int, int, int, int, int, int, int, int]
    efficiency: PyShedsRaster
    nodata_out: Union[int, float]
    routing: str
    cycle_size: int
    algorithm: str


class TaudemFACInputDict(TypedDict):
    fdr: str
    outFl: str
    cores: int
    mpiCall: str
    mpiArg: str


class TaudemDistance_to_streamInputDict(TypedDict):
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


TauDEMDict = Union[
    TaudemFACInputDict,
    TaudemDistance_to_streamInputDict,
    TaudemMaxUpslopeInputDict,
]
