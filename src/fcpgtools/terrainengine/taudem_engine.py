import os
import traceback
import subprocess
import pathlib
from tempfile import tempdir
from typing import List, Union
from pathlib import Path
import xarray as xr
from src.fcpgtools.types import Raster, TauDEMDict
from src.fcpgtools.utilities import intake_raster, save_raster

#TODO: Find what to do about saving temporary files
TEMP_DIR = Path(r'C:\Users\xrnogueira\Downloads')

def _taudem_prepper(
    in_raster: Raster,
    ) -> str:
    """
    Converts an input raster into a TauDEM compatible path string. 
    If param:in_raster is a xr.DataArray, it is saved in a temporary location.
    """
    if isinstance(in_raster, xr.DataArray):
        temp_path = TEMP_DIR / 'fdr_d8_temp.tif'
        save_raster(in_raster, temp_path)
        in_raster = str(temp_path)
    elif isinstance(in_raster, pathlib.PathLike):
        in_raster = str(in_raster)
    else:
        # No support for raw string in cmd line tools!
        print('ERROR: param:d8_fdr must be a xr.DataArray of a PathLike object.')
        #TODO: Handle exceptions
        raise Exception
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
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) the Flow Accumulation Cells (FAC) raster as a xarray DataArray object.
    """
    #TODO: Implement upstream pour points using weighting grid!
    
    d8_fdr = _taudem_prepper(d8_fdr)
    save = False
    if out_path is None:
        out_path = TEMP_DIR / 'fac_temp.tif'
    else: save = True

    taudem_dict = {
        'fdr': d8_fdr,
        'outFl': str(out_path),
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }

    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    # use TauDEM via subprocess to make a Flow Accumulation Raster
    try:
        cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} -nc'.format(
            **taudem_dict)
        _ = subprocess.run(cmd, shell=True)

    except:
        #TODO: Handle exceptions
        print('ERROR: TauDEM AreaD8 failed!')
        traceback.print_exc()
    
    out_raster = intake_raster(out_path)
    #FIXME: if not save: os.remove(out_path)
    return out_raster

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
    :param fdr: (str) path to flow direction raster in TauDEM format.
    :param fac_raster: (str) path to flow accumulation raster.
    :param accum_threshold: (int) # of upstream/accumulated cells to consider classify a stream cell.
    :param out_path: (str, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) a raster with values of D8 flow distance from each cell to the nearest stream.
    """
    d8_fdr = _taudem_prepper(d8_fdr)
    fac_raster = _taudem_prepper(fac_raster)

    save = False
    if out_path is None:
        out_path = TEMP_DIR.parent / 'fac_temp.tif'
    else: save = True

    taudem_dict = {
        'fdr': d8_fdr,
        'fac': fac_raster,
        'outRast': out_path,
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

    except:
        #TODO: Handle exceptions
        print('ERROR: TauDEM d8hdisttostrm failed!')
        traceback.print_exc()

    out_raster = intake_raster(out_path)
    if not save: os.remove(out_path)
    return out_raster

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
        out_path = TEMP_DIR.parent / 'fac_temp.tif'
    else: save = True

    if not get_min_upslope:
        accum_type_str = ''
    else:
        accum_type_str = '-min'

    taudem_dict = {
        'fdr': d8_fdr,
        'param': param_raster,
        'outRast': out_path,
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

    except:
        #TODO: Handle exceptions
        print('ERROR: TauDEM d8flowpathextremeup failed!')
        traceback.print_exc()

    out_raster = intake_raster(out_path)

    #TODO: Add stream mask function!

    if not save: os.remove(out_path)
    return out_raster


#TODO: Return to decay. The first function should be in tools.py.
# The TauDEM command relies on a D-inf raster, which we also need to add to tools.py/
def decay_raster() -> xr.DataArray:
    raise NotImplementedError

def decay_decay_accumulation() -> xr.DataArray:
    raise NotImplementedError

# NON_REFACTORED, FOR REFERENCE
def decayAccum(
    ang,
    mult,
    outRast,
    paramRast=None,
    cores=1,
    mpiCall='mpiexec',
    mpiArg='-n',
    verbose=False,
    ) -> xr.DataArray:
    """Decay the accumulation of a parameter raster.

    Parameters
    ----------
    ang : str
        Path to flow angle raster from the TauDEM D-Infinity flow direction tool.
    mult : str
        Path to raster of multiplier values applied to upstream accumulations,
        1 corresponds to no decay, 0 corresponds to complete decay.
    outRast : str
        Path to output raster for decayed accumulation raster.
    paramRast : str (optional)
        Raster of parameter values to accumulate. If not supplied area will be accumulated. Defaults to None.
    cores : int (optional)
        Number of cores to use. Defaults to 1.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter, defaults to '-n'.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster
        Decayed accumulation raster, either area or parameter depending on what is supplied to the function.
    """
    if paramRast != None:
        try:
            if verbose: print('Accumulating parameter')
            tauParams = {
                'ang': ang,
                'cores': cores,
                'dm': mult,
                'dsca': outRast,
                'weight': paramRast,
                'mpiCall': mpiCall,
                'mpiArg': mpiArg
            }

            cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -wg {weight} -nc'.format(
                **tauParams)  # Create string of tauDEM shell command
            if verbose: print(cmd)
            result = subprocess.run(cmd, shell=True)  # Run shell command
            result.stdout
            if verbose: print("Parameter accumulation written to: {0}".format(outRast))

        except:
            print('Error Accumulating Data')
            traceback.print_exc()
    else:
        try:
            if verbose: print('Accumulating parameter')
            tauParams = {
                'ang': ang,
                'cores': cores,
                'dm': mult,
                'dsca': outRast,
                'mpiCall': mpiCall,
                'mpiArg': mpiArg
            }

            cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -nc'.format(
                **tauParams)  # Create string of tauDEM shell command
            if verbose: print(cmd)
            result = subprocess.run(cmd, shell=True)  # Run shell command
            result.stdout
            if verbose: print("Parameter accumulation written to: {0}".format(outRast))

        except:
            print('Error Accumulating Data')
            traceback.print_exc()
