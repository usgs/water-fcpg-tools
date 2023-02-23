"""Python protocols defining the input/output signature of terrain engine functions.

This module stores abstract methods for all tools.py functions that require 
a terrain engine. Nesting these methods in @runtime_checkable classes that 
inherit from typing.Protocol allows function signatures to be verified via our 
engine_validator.validate_engine decorator.

For more information on Python Protocols see:
https://peps.python.org/pep-0544/
"""

import abc
from pathlib import Path
import xarray as xr
from typing import Protocol, Union, Optional, runtime_checkable
from fcpgtools.custom_types import Raster, PourPointValuesDict


@runtime_checkable
class SupportsAccumulateFlow(Protocol):

    @abc.abstractmethod
    def accumulate_flow(
        d8_fdr: Raster,
        upstream_pour_points: Optional[PourPointValuesDict] = None,
        weights: Optional[xr.DataArray] = None,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Create a Flow Accumulation Cell (FAC) raster from a D8 Flow Direction Raster.

        Args:
            d8_fdr: A  D8 Flow Direction Raster (dtype=Int).
            upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
                and updated cell values as the second [1].
                This allows the FAC to be made with boundary conditions such as upstream basin pour points.
            weights: A grid defining the value to accumulate from each cell. Default is a grid of 1s.
            out_path: Defines a path to save the output raster.
            **kwargs: keyword arguments, specific options depend on the engine being used.

        Returns:
            The output Flow Accumulation Cells (FAC) raster.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsAccumulateParameter(Protocol):

    @abc.abstractmethod
    def accumulate_parameter(
        d8_fdr: Raster,
        parameter_raster: Raster,
        upstream_pour_points: Optional[PourPointValuesDict] = None,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Create a parameter accumulation raster from a D8 Flow Direction Raster and a parameter raster.

        A key aspect of this function is that the output DataArray will have dimensions matching param:parameter_raster.

        Args:
            d8_fdr: A D8 Flow Direction Raster (dtype=Int).
            parameter_raster: A parameter raster aligned via tools.align_raster() with the us_fdr. 
                This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
            upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
                and updated cell values as the second [1].
                This allows the FAC to be made with boundary conditions such as upstream basin pour points.
            out_path: Defines a path to save the output raster.
            **kwargs: keyword arguments, specific options depend on the engine being used.

        Returns:
            The output parameter accumulation raster.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsExtremeUpslopeValues(Protocol):

    @abc.abstractmethod
    def extreme_upslope_values(
        d8_fdr: Raster,
        parameter_raster: Raster,
        mask_streams: Optional[Raster] = None,
        out_path: Optional[Union[str, Path]] = None,
        get_min_upslope: bool = False,
        **kwargs,
    ) -> xr.DataArray:
        """Finds the max (or min if get_min_upslope=True) value of a parameter grid upstream from each cell in a D8 FDR raster.

        NOTE: Replaces tools.ExtremeUpslopeValue() from V1 FCPGtools.

        Args:
            d8_fdr: A flow direction raster .
            parameter_raster: A parameter raster to find the max values from.
            mask_streams: A stream mask raster from tools.mask_streams(). If provided, the output will be masked to only stream cells.
            out_path: Defines a path to save the output raster.
            get_min_upslope: If True, the minimum upslope value is assigned to each cell.
            **kwargs: keyword arguments, specific options depend on the engine being used.

        Returns:
            A raster with max (or min) upstream value of the parameter grid as each cell's value.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsDistanceToStream(Protocol):

    @abc.abstractmethod
    def distance_to_stream(
        d8_fdr: Raster,
        fac_raster: Raster,
        accum_threshold: int,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Calculates distance each cell is from a stream (as defined by a cell accumulation threshold).

        NOTE: Replaces tools.dist2stream() from V1 FCPGtools.

        Args:
            d8_fdr: A D8 Flow Direction Raster (dtype=Int).
            fac_raster: A Flow Accumulation Cell (FAC) raster output from accumulate_flow().
            accum_threshold: The # of upstream/accumulated cells to consider a cell a stream.
            out_path: Defines a path to save the output raster.
            **kwargs: keyword arguments, specific options depend on the engine being used.

        Returns:
            A raster with values of D8 flow distance from each cell to the nearest stream.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsDecayAccumulation(Protocol):

    @abc.abstractmethod
    def decay_accumulation(
        d8_fdr: Raster,
        decay_raster: Raster,
        upstream_pour_points: Optional[PourPointValuesDict] = None,
        parameter_raster: Optional[Raster] = None,
        out_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> xr.DataArray:
        """Creates a D-Infinity based accumulation raster (parameter or cell accumulation) while applying decay via a multiplier_raster.

        NOTE: Replaces tools.decayAccum() from V1 FCPGtools.

        Args:
            dinf_fdr: A flow direction raster in D-Infinity format. This input can be made with tools.d8_to_dinfinity().
            decay_raster: A decay 'multiplier' raster calculated from distance to stream via tools.make_decay_raster().
            upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
                and updated cell values as the second [1].
                This allows the FAC to be made with boundary conditions such as upstream basin pour points.
            parameter_raster: A parameter raster aligned via tools.align_raster() with the us_fdr. 
                This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
            out_path: Defines a path to save the output raster.
            **kwargs: keyword arguments, specific options depend on the engine being used.

        Returns:
            The output decayed accumulation raster.
        """
        raise NotImplementedError
