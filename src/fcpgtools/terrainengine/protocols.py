import abc
import xarray as xr
import geopandas as gpd
from typing import Protocol, Union, List, Dict
from src.fcpgtools.types import Raster

class SupportsFDRtoFAC(Protocol):
    """"""

    @abc.abstractmethod
    def fac_from_fdr(
            d8_fdr: Raster, 
            upstream_pour_points: List = None,
            out_path: str = None,
        ) -> xr.DataArray:
        """
        Create a Flow Accumulation Cell (FAC) raster from a TauDEM format D8 Flow Direction Raster.
        :param d8_fdr: (xr.DataArray or str raster path) a TauDEM format D8 Flow Direction Raster (dtype=Int).
        :param upstream_pour_points: (list, default=None) a list of lists each with with coordinate tuples
            as the first item [0], and updated cell values as the second [1]. This allows the FAC to be made
            with boundary conditions such as upstream basin pour points.
        :param out_path: (str, default=None) defines a path to save the output raster.
        :returns: (xr.DataArray) the Flow Accumulation Cells (FAC) raster as a xarray DataArray object.
        """
        raise NotImplementedError


class SupportsParameterAccumulation(Protocol):
    """"""

    @abc.abstractmethod
    def parameter_accumulation(
            param_raster: Raster, 
            fac_raster: Raster,
            update_input: Union[Dict,List] = None, 
            update_add: bool = False,
            out_path: str = None
        ) -> xr.DataArray:
        """
        Create a accumulation raster from an arbitrary parameter raster.
        :param param_raster: (xr.DataArray or str raster path)
        :param fac_raster: (xr.DataArray or str raster path) the Flow Accumulation Cells (FAC) raster.
        :param update_input: (dict or list, optional) allows boundary conditions to be set by updating the
            input param:param_raster with upstream pour point accumulation sums. Either a list of lists or a dictionary.
            with integer keys to reference band index storing list[coords:tuple, value:Union[float, int]].
            Note: if the input is multi-dimensional this must be a dictionary.
        :param add_update: (bool, default=False) if True while update_raster!=None, the update_raster dict
                values are added to the parameter raster value instead of replacing them.
        :param out_path: (str, default=None) defines a path to save the output raster.
        :returns: (xr.DataArray) the parameter accumulation raster as a xarray DataArray object.
        """
        raise NotImplementedError


class SupportsMaxUpslope(Protocol):
    """"""

    @abc.abstractmethod
    def get_max_upslope(
            fdr: Raster, 
            param_raster: Raster, 
            get_min: bool = False,
            out_path: str = None, 
            mask_raster: Raster = None,
        ) -> xr.DataArray:
        """
        Gets a max/min value from param:param_raster from the subset of all upslope cells for each cell in a FDR.
        In TauDEM this is the "Extreme Upslope Value" function.
        :param fdr: (xr.DataArray or str raster path) a TauDEM encoded D8 Flow Direction Raster (FDR).
        :param param_raster: (xr.DataArray or str raster path) a raster with overlapping extent as param:fdr fromw which
            extreme upslope values are pulled from (i.e., a DEM raster).
        :param get_min: (bool, default=False) if True, the minimum param:param_raster value is returned from all upslope cells.
        :param out_path: (str path, default=None) defines a path to save the output raster.
        :param mask_raster: (xr.DataArray or str raster path) a dtype=int raster where cell values = 1 indicate areas to return values
            for in the output (i.e., a stream mask to show the max elevation upslope of each part of a stream network).
        :returns: (xarray.DataArray) the output raster with extreme upslope values as a DataArray object in memory.
        """
        raise NotImplementedError


class SupportsDistanceToStream(Protocol):
    """"""

    @abc.abstractmethod
    def distance_to_stream(
            fdr: Raster, 
            stream_mask: Raster,
            out_path: str = None
        ) -> xr.DataArray:
        """
        Create a raster where cell values represent the horizantal distance to the nearest stream ALONG the flow path.
        :param fdr: (xr.DataArray or str raster path) a TauDEM encoded D8 Flow Direction Raster (FDR).
        :param stream_mask: (xr.DataArray or str raster path) a binary raster where value=1 where for stream cells
            as designated by meeting some flow accumulation threshold. Output of pyfunc:value_mask(thresh=int/float).
        :param out_path: (str path, default=None) defines a path to save the output raster.
        :returns: (xr.DataArray) a raster with cell value equal to the horizantal length along the flow path to the
            the nearest stream cell.
        """
        raise NotImplementedError
        

class SupportsDecayRaster(Protocol):
    """"""

    @abc.abstractmethod
    def decay_raster(
            distance_to_stream_raster: Raster, 
            decay_constant: Union[float,int] = 2,
            out_path: str = None,
        ) -> xr.DataArray:
        """
        Creates a decay weight raster based on distance to stream and a decay factor. The output raster
            has values ranging from 0 (total decay) to 1 (no decay) and is intended to be used in pyfunc:decay_accumulation().
            Note: output cell value: np.exp((-1 * dist2stream_raster * cell_size) / (cell_size ** decay_constant))`
        :param dist2stream_raster: (xr.DataArray or str raster path) a raster with cell value equal to the flow path to the
            the nearest stream cell. This raster is output from pyfunc:calculate_dsit2stream().
        :param decay_constant: (float or int) the decay constant in the decay formula.
            Set k to 2 for "moderate" decay; greater than 2 for slower decay; or less than 2 for faster decay.
        :param out_path: (str path, default=None) defines a path to save the output raster.
        :returns: (xr.DataArray) the output decay weighting raster as an xarray DataArray.
        """
        raise NotImplementedError


class SupportsDecayAccumulation(Protocol):
    """"""
    @abc.abstractmethod
    def decay_accumulation(
            dinf_fdr:  Raster, 
            decay_raster:  Raster,
            param_raster:  Raster, 
            out_path: str = None,
        ) -> xr.DataArray:
        """
        Create a decayed accumulation raster from a D-Infinity FDR.
        In TauDEM this is "D-Infinity Decaying Accumulation" function.
        :param dinf_fdr: (xr.DataArray or str raster path) a D-Infinity Flow Direction Raster (FDR).
        :param decay_raster: (xr.DataArray or str raster path) a dist2stream based decay raster (dtype=float, values 0-1).
            Note: this is the output of pyfunc:make_decay_raster().
        :param param_raster: (xr.DataArray or str raster path, default=None) a raster to accumulate.
            if None, this function produces a D-Infinity decayed FAC.
        :param out_path: (str path, default=None) defines a path to save the output raster.
        :returns: (xr.DataArray) the output decayed accumulation raster as an xarray DataArray.
        """
        raise NotImplementedError