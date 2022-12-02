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
    _combine_split_bands, _split_bands, update_parameter_raster, _verify_alignment, _replace_nodata_value
from fcpgtools.tools import prep_parameter_grid, value_mask, d8_to_dinf

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
                prefix='taudem_temp_input',
                suffix='.tif',
                ).name
            )
        save_raster(in_raster, temp_path)
        in_raster = str(temp_path)

    elif isinstance(in_raster, pathlib.PathLike):
        in_raster = str(in_raster)
        
    else: raise TypeError('ERROR: param:d8_fdr must be a xr.DataArray of a PathLike object.')
    
    if temp_path.exists(): return in_raster
    else: return FileNotFoundError('ERROR: Failed to create temporary file!')

def _update_taudem_dict(
    taudem_dict: TauDEMDict,
    kwargs: dict = None,
    ) -> TauDEMDict:
    if len(kwargs) != 0:
        for key, value in kwargs.items():
            if key in taudem_dict.keys():
                taudem_dict.update(key, value)
            else:
                print(f'WARNING: Kwarg argument {key} is invalid.')
    return taudem_dict

def _clear_temp_files(
    prefixs: Union[str, List[str]],
    directory: Path = Path.cwd(),
    ) -> None:
    """
    Deletes all files with a given prefix in a directory
    :param prefixs: (str or list of str)
    :param directory: (pathlike directory, default=current working directory) directory to look within.
    :returns: None
    """
    if directory != Path.cwd():
        if not directory.is_dir(): raise TypeError(f'ERROR: param:dir={str(directory)} is not a valid directory!')
    if isinstance(prefixs, str): prefixs = [prefixs]

    # delete files with matching prefixes
    for file in directory.iterdir():
        try:
            remove = False
            for prefix in prefixs:
                if prefix in str(file): remove = True
            if remove: file.unlink()
        except PermissionError: pass # print('WARNING: Could not delete temp files due to a PermissionError')
    return None

def fac_from_fdr(
    d8_fdr: Raster,
    upstream_pour_points: List = None,
    weights: xr.DataArray = None,
    out_path: Union[str, Path] = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Create a Flow Accumulation Cell (FAC) raster from a TauDEM format D8 Flow Direction Raster.
        Note: this is a command line wrapper of TauDEM:aread8.
    :param d8_fdr: (xr.DataArray or str raster path) a TauDEM format D8 Flow Direction Raster (dtype=Int).
    :param upstream_pour_points: (list, default=None) a list of lists each with with coordinate tuples
        as the first item [0], and updated cell values as the second [1]. This allows the FAC to be made
        with boundary conditions such as upstream basin pour points.
    :param out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.
    :param out_dtype: (np.dtype) allows the output raster dtype to match a parameter grids.
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

    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='fac_temp',
                suffix='.tif',
                ).name
            )
    elif isinstance(out_path, str): out_path = Path(out_path)

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

    # remove temporary files and return output
    out_raster.close()
    _clear_temp_files(prefixs=['fac_temp'])

    return out_raster

def parameter_accumulate( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: List = None,
    out_path: Union[str, Path] = None,
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
    :param out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.
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
    else: out_raster = list(out_dict.items())[0][1] 
    out_raster.name = 'Parameter_Accumulate'

    # save if necessary and remove temp files
    if isinstance(out_path, str): out_path = Path(out_path)
    if out_path is not None:
        save_raster(out_raster, out_path)

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input'])

    return out_raster

def distance_to_stream(
    d8_fdr: Raster,
    fac_raster: Raster,
    accum_threshold: int = None,
    out_path: Union[str, Path] = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Calculates distance each cell is from a stream (as defined by a cell accumulation threshold).
        Note: this is a command line wrapper of TauDEM:aread8.
    :param fdr: (xr.DataArray or path str) path to flow direction raster in TauDEM format.
    :param fac_raster: (xr.DataArray or path str) path to flow accumulation raster.
    :param accum_threshold: (int) # of upstream/accumulated cells to consider classify a stream cell.
    :param out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns: (xr.DataArray) a raster with values of D8 flow distance from each cell to the nearest stream.
    """
    d8_fdr = _taudem_prepper(d8_fdr)

    # get stream grid as a taudem tempfile
    fac_raster = intake_raster(fac_raster)
    fac_raster = fac_raster.fillna(0)
    fac_raster = fac_raster.rio.write_nodata(0)
    fac_raster = fac_raster.astype('int')
    fac_raster = _taudem_prepper(fac_raster)

    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='dist2stream_temp',
                suffix='.tif',
                ).name
            )
    elif isinstance(out_path, str): out_path = Path(out_path)

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

    cmd = '{mpiCall} {mpiArg} {cores} D8HDistTostrm -p {fdr} -src {fac} -dist {outRast} -thresh {thresh}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['outRast']).exists():
        raise FileNotFoundError('ERROR: TauDEM D8HDistTostrm failed to create an output!')    

    # update nodata values
    out_raster = intake_raster(out_path)
    out_raster = _replace_nodata_value(out_raster, np.nan)

    # clear temporary files and return the output
    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'dist2stream_temp'])

    return out_raster

def _ext_upslope_cmd(
    d8_fdr_path: str,
    parameter_raster: xr.DataArray,
    accum_type_str_path: str,
    kwargs: dict = None,
    ) -> xr.DataArray:
    """Back end function that makes TauDEM cmd line call for D8FlowPathExtremeUp"""

    parameter_raster_path = _taudem_prepper(parameter_raster)

    # make temporary output path
    out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='ext_upslope_temp',
                suffix='.tif',
                ).name
            )

    taudem_dict = {
        'fdr': d8_fdr_path,
        'param': parameter_raster_path,
        'outRast': str(out_path),
        'accum_type': accum_type_str_path,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }
    
    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    cmd = '{mpiCall} {mpiArg} {cores} D8FlowPathExtremeUp -p {fdr} -sa {param} -ssa {outRast} {accum_type} -nc'.format(
        **taudem_dict)  # Create string of tauDEM shell command
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['outRast']).exists():
        raise FileNotFoundError('ERROR: TauDEM D8FlowPathExtremeUp failed to create an output!')

    out_raster = intake_raster(Path(taudem_dict['outRast']))

    # update nodata and convert -9999 values to nodata
    out_raster = out_raster.where(
        (out_raster != -9999),
        out_raster.rio.nodata,
        )
    out_raster = _replace_nodata_value(
        out_raster,
        np.nan,
        )

    out_raster.close()
    _clear_temp_files(prefixs=['ext_upslope_temp'])
    return out_raster

def get_max_upslope(
    d8_fdr: Raster,
    parameter_raster: Raster,
    stream_mask: Raster = None,
    out_path: Union[str, Path] = None,
    get_min_upslope: bool = False,
    **kwargs,
    ) -> xr.DataArray:
    """
    Finds the max (or min if get_min_upslope=True) value of a parameter grid upstream
        from each cell in a D8 FDR raster (with TauDEM direction format).
        Note: This is a wrapper for the TauDEM's d8flowpathextremeup.
    :param d8_fdr: (xr.DataArray or path str) path to flow direction raster in TauDEM format.
    :param parameter_raster: (xr.DataArray or path str) a parameter raster to find the max values from.
    :param stream_mask: (optional, xr.DataArray or path str) a stream mask raster from tools.stream_mask().
        If provided, the output will be masked to only stream cells.
    :param out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.
    :returns: (xr.DataArray) raster with max (or min) upstream value of the 
        parameter grid as each cell's value.
    """
    d8_fdr = _taudem_prepper(d8_fdr)
    parameter_raster = intake_raster(parameter_raster)
    accum_type_str = '-min' if get_min_upslope else ''

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2:
        raster_bands = _split_bands(parameter_raster)
    else:
        raster_bands = {(0, 0): parameter_raster}

    # create extream upslope value rasters for each parameter raster band
    out_dict = {}
    for index_tuple, array in raster_bands.items():
        i, dim_name = index_tuple

        upslope_raster = _ext_upslope_cmd(
            d8_fdr,
            array,
            accum_type_str,
            kwargs=kwargs,
            )

        out_dict[(i, dim_name)] = upslope_raster

    # re-combine into DataArray
    if len(out_dict.keys()) > 1:
        out_raster =  _combine_split_bands(out_dict)
    else: out_raster = list(out_dict.items())[0][1] 
    out_raster.name = f'{accum_type_str[1:]}_upslope_values'
    
    # apply stream mask if necessary
    if stream_mask is not None:
        if _verify_alignment(out_raster, stream_mask):
            out_raster = out_raster.where(
                (stream_mask != stream_mask.rio.nodata),
                np.nan,
                )
        else:
            print('WARNING: Stream mask does not align with extream upslope value output! '
            'No mask is applied.')
    
    # update nodata values
    out_raster = _replace_nodata_value(out_raster, np.nan)

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'ext_upslope_temp'])
    return out_raster

def _decay_accumulation_cmd(
    dinf_fdr_path: str,
    decay_raster_path: str,
    weights: xr.DataArray = None,
    kwargs: dict = None,
    ) -> xr.DataArray:

    weights_path = _taudem_prepper(weights)

    # make temporary output path
    out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='decay_accum_temp',
                suffix='.tif',
                ).name
            )

    # build the input dictionary
    taudem_dict = {
        'dinf_fdr_path': dinf_fdr_path,
        'dm': decay_raster_path,
        'dsca': str(out_path),
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
        }

    if weights is not None: taudem_dict['finalArg'] = f'-wg {str(weights_path)} -nc'
    else: taudem_dict['finalArg'] = '-nc'

    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    # use TauDEM via subprocess to make a decay accumulation raster
    cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {dinf_fdr_path} -dm {dm} -dsca {dsca} {finalArg}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['dsca']).exists():
        raise FileNotFoundError('ERROR: TauDEM dinfdecayaccum failed to create an output!')

    out_raster = intake_raster(Path(taudem_dict['dsca']))

    # update nodata and convert -9999 values to nodata
    out_raster = out_raster.where(
        (out_raster != -9999),
        out_raster.rio.nodata,
        )
    out_raster = _replace_nodata_value(
        out_raster,
        np.nan,
        )

    out_raster.close()
    _clear_temp_files(prefixs=['decay_accum_temp'])
    return out_raster

def decay_accumulation(
    d8_fdr: Raster,
    decay_raster: Raster,
    upstream_pour_points: List = None,
    parameter_raster: Raster = None,
    out_path: Union[str, Path] = None,
    **kwargs,
    ) -> xr.DataArray:
    """
    Creates a D-Infinity based accumulation raster (parameter or cell accumulation) while applying decay via a multiplier_raster.
        Note: This is a command line wrapper of TauDEM:DinfDecayAccum.
    :param dinf_fdr: (xr.DataArray or str raster path) path to flow direction raster in D-Infinity format.
        Note: This input can be made with tools.d8_to_dinf().
    :param multiplier_raster: (xr.DataArray or str raster path)
    :param parameter_raster: (optional, xr.DataArray or str raster path)
    :param out_path: (str or pathlib.Path, default=None) defines a path to save the output raster.
    :param **kwargs: can pass in optional values using "cores", "mpiCall", "mpiArg" TauDem arguments.
    :returns:
    """
    # prep data for taudem
    d8_fdr = intake_raster(d8_fdr)
    dinf_fdr = d8_to_dinf(d8_fdr)
    
    dinf_fdr_path = _taudem_prepper(dinf_fdr)
    decay_raster_path = _taudem_prepper(decay_raster)

    # prep parameter raster and boundary conditions
    weights = None
    if parameter_raster is not None: weights = intake_raster(parameter_raster)
    elif upstream_pour_points is not None:
        weights = xr.zeros_like(
            dinf_fdr,
            dtype=np.dtype('float64'),
            ) + 1
    if weights is not None:
        if upstream_pour_points is not None:
            weights = update_parameter_raster(
                weights,
                d8_fdr,
                upstream_pour_points,
                )
        weights = prep_parameter_grid(
            weights,
            dinf_fdr,
            np.nan,
            )

        # calculate decay raster and split if multi-dimensional
        if len(weights.shape) > 2:
            raster_bands = _split_bands(weights)
        else:
            raster_bands = {(0, 0): weights}

        # create extream upslope value rasters for each parameter raster band
        out_dict = {}
        for index_tuple, array in raster_bands.items():
            i, dim_name = index_tuple

            decay_acc_raster = _decay_accumulation_cmd(
                dinf_fdr_path,
                decay_raster_path,
                array,
                kwargs,
                )

            out_dict[(i, dim_name)] = decay_acc_raster

        # re-combine into DataArray
        if len(out_dict.keys()) > 1:
            out_raster =  _combine_split_bands(out_dict)
        else: out_raster = list(out_dict.items())[0][1] 
        
    else:
        out_raster = _decay_accumulation_cmd(
            dinf_fdr_path,
            decay_raster_path,
            weights=None,
            kwargs=kwargs,
            )
    out_raster.name = 'decay_accumulation_raster'

    # update nodata values
    out_raster = _replace_nodata_value(out_raster, np.nan)

    # save if necessary
    if out_path is not None:
        save_raster(out_raster, out_path)

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'decay_accum_temp'])
    return out_raster



