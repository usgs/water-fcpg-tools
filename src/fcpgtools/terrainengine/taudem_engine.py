import os
import tempfile
import traceback
import subprocess
import pathlib
from tempfile import tempdir
from typing import List, Union
from pathlib import Path
import numpy as np
import xarray as xr
from fcpgtools.types import Raster, TauDEMDict
from fcpgtools.utilities import intake_raster, save_raster, \
    _combine_split_bands, _split_bands, update_parameter_raster
from fcpgtools.tools import prep_parameter_grid

def _taudem_prepper(
    in_raster: Raster,
    ) -> str:
    """
    Converts an input raster into a TauDEM compatible path string. 
    If param:in_raster is a xr.DataArray, it is saved in a temporary location.
    """
    if isinstance(in_raster, xr.DataArray):
        temp_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='fdr_to_fac_temp',
                suffix='.tif',
                ).name
            )
        save_raster(in_raster, temp_path)
        in_raster = str(temp_path)

    elif isinstance(in_raster, pathlib.PathLike):
        in_raster = str(in_raster)
        
    else:
        # No support for raw string in cmd line tools!
        print('ERROR: param:d8_fdr must be a xr.DataArray of a PathLike object.')
        #TODO: Handle exceptions
        raise TypeError
    return in_raster

def _update_taudem_dict(
    taudem_dict: TauDEMDict,
    kwargs: dict
    ) -> TauDEMDict:
    if kwargs:
        for key, value in kwargs.items():
            if key in taudem_dict.keys():
                taudem_dict.update(key, value)
            else:
                print(f'WARNING: Kwarg argument {key} is invalid.')
    return taudem_dict

def fac_from_fdr(
    d8_fdr: Raster,
    upstream_pour_points: List = None,
    weights: xr.DataArray = None,
    out_dtype: np.dtype = np.dtype('int64'),
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Create a Flow Accumulation Cell (FAC) raster from a TauDEM format D8 Flow Direction Raster.
        Note: this is a command line wrapper of TauDEM:aread8.
    :param d8_fdr: (xr.DataArray or str raster path) a TauDEM format D8 Flow Direction Raster (dtype=Int).
    :param upstream_pour_points: (list, default=None) a list of lists each with with coordinate tuples
        as the first item [0], and updated cell values as the second [1]. This allows the FAC to be made
        with boundary conditions such as upstream basin pour points.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param out_dtype) (np.dtype) allows the output raster dtype to match a parameter grids.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) the Flow Accumulation Cells (FAC) raster as a xarray DataArray object.
    """
    d8_fdr_path = _taudem_prepper(d8_fdr)

    # get tempoarary files for necessary inputs
    if upstream_pour_points is None and weights is None:
        weight_path = ''
        wg = ''
    else:
        if weights is not None: weights = weights
        else:
            weights = xr.zeros_like(
                d8_fdr,
                dtype=np.dtype('float64'),
                ) + 1
            weights = update_parameter_raster(
                weights,
                upstream_pour_points,
                )
            weights = prep_parameter_grid(
                weights,
                d8_fdr,
                -1,
                )
        weight_path = _taudem_prepper(weights)
        wg = '-wg '

    save = False
    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='fac_temp',
                suffix='.tif',
                ).name
            )
    else: save = True

    taudem_dict = {
        'fdr': d8_fdr_path,
        'outFl': str(out_path),
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }

    if wg != '': taudem_dict['finalArg'] = f'{wg}{str(weight_path)} -nc'
    else: taudem_dict['finalArg'] = '-nc'

    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    # use TauDEM via subprocess to make a Flow Accumulation Raster
    cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} {finalArg}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)
    
    if not Path(taudem_dict['outFl']).exists():
        raise FileNotFoundError('ERROR: TauDEM areaD8 failed to create an output!')

    out_raster = intake_raster(Path(taudem_dict['outFl']))
    out_raster = out_raster.astype(np.float64)

    # convert out of bounds values to np.nan, in bounds nan to 0, and update nodata
    out_raster = out_raster.where(
        (out_raster != out_raster.rio.nodata),
        np.nan,
        )
    out_raster = out_raster.rio.write_nodata(np.nan)
    out_raster = out_raster.fillna(0)
    out_raster = out_raster.where(
        (d8_fdr.values != d8_fdr.rio.nodata),
        np.nan,
        )
    return out_raster

def parameter_accumulate( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: List = None,
    out_path: str = None,
    ) -> xr.DataArray:
    """
    Create a parameter accumulation raster from a TauDEM format D8 Flow Direction Raster and a parameter raster.
        Note: this is a command line wrapper of TauDEM:aread8.
    :param d8_fdr: (xr.DataArray or str raster path) a TauDEM format D8 Flow Direction Raster (dtype=Int).
    :param parameter_raster: (xr.DataArray or str raster path) a parameter raster aligned via tools.align_raster()
        with the us_fdr. 
        Note: This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
    :param upstream_pour_points: (list, default=None) a list of lists each with with coordinate tuples
        as the first item [0], and updated cell values as the second [1]. This allows the FAC to be made
        with boundary conditions such as upstream basin pour points.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) the parameter accumulation raster as a xarray DataArray object.
    """
    d8_fdr = intake_raster(d8_fdr)
    parameter_raster = prep_parameter_grid(
        parameter_raster=parameter_raster,
        fdr_raster=d8_fdr,
        out_of_bounds_value=-1,
        )

    # add any pour point accumulation via utilities.update_parameter_raster()
    if upstream_pour_points is not None: parameter_raster = update_parameter_raster(
        parameter_raster,
        upstream_pour_points,
        )

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2:
        raster_bands = _split_bands(parameter_raster)
    else:
        raster_bands = {(0, 0): parameter_raster}

    # create weighted accumulation rasters
    out_dict = {}
    for index_tuple, array in raster_bands.items():
        i, dim_name = index_tuple

        accumulated = fac_from_fdr(
            d8_fdr,
            weights=array,
            out_dtype=array.dtype,
            )

        out_dict[(i, dim_name)] = accumulated

    # re-combine into DataArray
    if len(out_dict.keys()) > 1:
        out_raster =  _combine_split_bands(out_dict)
    else: out_raster =  list(out_dict.items())[0][1] 

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)
    
    return out_raster

#TODO: test out, make sure it works in a variety of settings
def distance_to_stream(
    d8_fdr: Raster,
    fac_raster: Raster,
    accum_threshold: int = None,
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Calculates distance each cell is from a stream (as defined by a cell accumulation threshold).
        Note: this is a command line wrapper of TauDEM:aread8.
    :param fdr: (xr.DataArray or path str) path to flow direction raster in TauDEM format.
    :param fac_raster: (xr.DataArray or path str) path to flow accumulation raster.
    :param accum_threshold: (int) # of upstream/accumulated cells to consider classify a stream cell.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) a raster with values of D8 flow distance from each cell to the nearest stream.
    """
    d8_fdr = _taudem_prepper(d8_fdr)
    fac_raster = _taudem_prepper(fac_raster)

    save = False
    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='fac_temp',
                suffix='.tif',
                ).name
            )
    else: save = True

    taudem_dict = {
        'fdr': d8_fdr,
        'fac': fac_raster,
        'outRast': str(out_path),
        'thresh': accum_threshold,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }
    
    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    try:
        cmd = '{mpiCall} {mpiArg} {cores} d8hdisttostrm -p {fdr} -src {fac} -dist {outRast}, -thresh {thresh}'.format(
            **taudem_dict)
        _ = subprocess.run(cmd, shell=True)

    except Exception:
        #TODO: Handle exceptions
        print('ERROR: TauDEM d8hdisttostrm failed!')
        traceback.print_exc()

    out_raster = intake_raster(taudem_dict['outRast'])
    return out_raster

#TODO: test out, make sure it works in a variety of settings
def get_max_upslope(
    d8_fdr: Raster,
    param_raster: Raster,
    stream_mask: Raster = None,
    out_path: str = None,
    get_min_upslope: bool = False,
    **kwargs,
    ) -> xr.DataArray:
    """
    Finds the max (or min if get_min_upslope=True) value of a parameter grid upstream
        from each cell in a D8 FDR raster (with TauDEM direction format).
        Note: This is a wrapper for the TauDEM's d8flowpathextremeup.
    :param d8_fdr: (xr.DataArray or path str) path to flow direction raster in TauDEM format.
    :param param_raster: (xr.DataArray or path str) a parameter raster to find the max values from.
    :param stream_mask: (optional, xr.DataArray or path str) a stream mask raster from tools:stream_mask().
        If provided, the output will be masked to only stream cells.
    :param out_path: (str)
    :returns: (xr.DataArray) raster with max (or min) upstream value of the 
        parameter grid as each cell's value.
    """
    d8_fdr = _taudem_prepper(d8_fdr)
    param_raster = _taudem_prepper(param_raster)

    save = False
    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='fac_temp',
                suffix='.tif',
                ).name
            )
    else: save = True

    accum_type_str = '-min' if get_min_upslope else ''
    
    taudem_dict = {
        'fdr': d8_fdr,
        'param': param_raster,
        'outRast': str(out_path),
        'accum_type': accum_type_str,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }
    
    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    try:
        cmd = '{mpiCall} {mpiArg} {cores} d8flowpathextremeup -p {fdr} -sa {param} -ssa {outFl} {accum_type} -nc'.format(
            **taudem_dict)  # Create string of tauDEM shell command
        _ = subprocess.run(cmd, shell=True)

    except Exception:
        #TODO: Handle exceptions
        print('ERROR: TauDEM d8flowpathextremeup failed!')
        traceback.print_exc()

    out_raster = intake_raster(taudem_dict['outRast'])

    #TODO: Add stream mask function!
    return out_raster


#TODO: Return to decay. The first function should be in tools.py.
# The TauDEM command relies on a D-inf raster, which we also need to add to tools.py/
def decay_raster() -> xr.DataArray:
    raise NotImplementedError

def decay_accumulation(
    dinf_fdr: Raster,
    multiplier_raster: Raster,
    parameter_raster: Raster = None,
    out_path: str = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Creates a D-Infinity based accumulation raster (parameter or cell accumulation) while applying decay via a multiplier_raster.
        Note: This is a command line wrapper of TauDEM:DinfDecayAccum.
    :param dinf_fdr: (xr.DataArray or str raster path) path to flow direction raster in D-Infinity format.
        Note: This input can be made with tools.d8_to_dinf().
    :param multiplier_raster: (xr.DataArray or str raster path)
    :param parameter_raster: (optional, xr.DataArray or str raster path)
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns:
    """
    # prep data for taudem
    dinf_fdr_path = _taudem_prepper(dinf_fdr)
    multiplier_raster_path = _taudem_prepper(multiplier_raster)

    # prep parameter raster is applicable
    if parameter_raster is not None:
        parameter_raster = intake_raster(parameter_raster)
        parameter_raster = prep_parameter_grid(
            prep_parameter_grid,
            out_of_bounds_value=-1
        )
        parameter_raster_path = _taudem_prepper(parameter_raster)

    # make temporary files as necessary
    out_write_path = str

    # build the input dictionary
    taudem_dict = {
        'dinf_fdr_path': dinf_fdr_path,
        'dm': multiplier_raster_path,
        'dsca': out_write_path,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }

    if parameter_raster is not None: taudem_dict['finalArg'] = f'-wg {str(parameter_raster_path)} -nc'
    else: taudem_dict['finalArg'] = '-nc'

    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    # use TauDEM via subprocess to make a Flow Accumulation Raster
    try:
        cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {dinf_fdr_path} -dm {dm} -dsca {dsca} {finalArg}'.format(
            **taudem_dict)
        _ = subprocess.run(cmd, shell=True)

    except Exception:
        #TODO: Handle exceptions
        print('ERROR: TauDEM AreaD8 failed!')
        traceback.print_exc()

