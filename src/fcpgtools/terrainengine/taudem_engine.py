import tempfile
import subprocess
import pathlib
import tempfile
from typing import List, Dict, Union, Optional
from pathlib import Path
import numpy as np
import xarray as xr
from fcpgtools.types import Raster, TauDEMDict, PourPointValuesDict
from fcpgtools.utilities import load_raster, save_raster, \
    _combine_split_bands, _split_bands, adjust_parameter_raster, _verify_alignment, change_nodata_value
from fcpgtools.tools import make_fac_weights, value_mask, d8_to_dinfinity, mask_streams

def _taudem_prepper(
    in_raster: Raster,
) -> str:
    """Converts an input raster into a TauDEM compatible path string.  Creates a temp file if necessary."""
    if isinstance(in_raster, xr.DataArray):
        temp_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='taudem_temp_input',
                suffix='.tif',
            ).name
        )
        save_raster(
            in_raster,
            temp_path,
        )
        in_raster = str(temp_path)

    elif isinstance(in_raster, pathlib.PathLike):
        in_raster = str(in_raster)
        
    else: raise TypeError('param:d8_fdr must be a xr.DataArray of a PathLike object.')
    
    if temp_path.exists(): return in_raster
    else: raise FileNotFoundError('Failed to create temporary file!')

def _update_taudem_dict(
    taudem_dict: TauDEMDict,
    kwargs_dict: Union[Dict[str, str], Dict[str, Dict[str, str]]],
) -> TauDEMDict:
    if 'kwargs' in kwargs_dict.keys(): kwargs_dict = kwargs_dict['kwargs']
    if len(kwargs_dict) != 0:
        for key, value in kwargs_dict.items():
            if key in taudem_dict.keys():
                taudem_dict.update({key: value})
            else: print(f'WARNING: Kwarg argument {key} is invalid.')
    return taudem_dict

def _clear_temp_files(
    prefixs: Union[str, List[str]],
    directory: Path = Path.cwd(),
) -> None:
    """Deletes all files with a given prefix(s) in a directory path."""
    if directory != Path.cwd() or not directory.is_dir(): raise TypeError(
        f'param:dir={str(directory)} is not a valid directory!'
    )
    if isinstance(prefixs, str): prefixs = [prefixs]

    # delete files with matching prefixes
    for file in directory.iterdir():
        try:
            remove = False
            for prefix in prefixs:
                if prefix in str(file): remove = True
            if remove: file.unlink()
        except PermissionError: print('WARNING: Could not delete temp files due to a PermissionError')

def accumulate_flow(
    d8_fdr: Raster,
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    weights: Optional[xr.DataArray] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Create a Flow Accumulation Cell (FAC) raster from a TauDEM format D8 Flow Direction Raster.
    
    NOTE: this is a command line wrapper of TauDEM:aread8 and replaces tools.tauFlowAccum() from V1 FCPGtools.

    Args:
        d8_fdr: A TauDEM format D8 Flow Direction Raster (dtype=Int).
        upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
            and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as upstream basin pour points.
        weights: A grid defining the value to accumulate from each cell. Default is a grid of 1s.
        out_path: Defines a path to save the output raster.
        **kwargs: Can pass in optional TauDEM:aread8 parameter values using "cores", "mpiCall", or "mpiArg" as keys.

    Returns:
        The output Flow Accumulation Cells (FAC) raster.
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
            weights = adjust_parameter_raster(
                weights,
                d8_fdr,
                upstream_pour_points,
            )
            weights = make_fac_weights(
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

    taudem_dict = _update_taudem_dict(
        taudem_dict,
        kwargs,
    )

    # use TauDEM via subprocess to make a Flow Accumulation Raster
    cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} {finalArg}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)
    
    if not Path(taudem_dict['outFl']).exists():
        raise FileNotFoundError('TauDEM areaD8 failed to create an output!')

    out_raster = load_raster(Path(taudem_dict['outFl']))
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

def accumulate_parameter( 
    d8_fdr: Raster, 
    parameter_raster: Raster,
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Create a parameter accumulation raster from a TauDEM format D8 Flow Direction Raster and a parameter raster.
    
    A key aspect of this function is that the output DataArray will have dimensions matching param:parameter_raster.
    NOTE: This is a command line wrapper of TauDEM:aread8 and replaces tools.accumulateParam() from V1 FCPGtools.

    Args:
        d8_fdr: A TauDEM format D8 Flow Direction Raster (dtype=Int).
        parameter_raster: A parameter raster aligned via tools.align_raster() with the us_fdr. 
            This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
        upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
            and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as upstream basin pour points.
        out_path: Defines a path to save the output raster.
        **kwargs: Can pass in optional TauDEM:aread8 parameter values using "cores", "mpiCall", or "mpiArg" as keys.

    Returns:
        The output parameter accumulation raster.
    """
    d8_fdr = load_raster(d8_fdr)
    parameter_raster = make_fac_weights(
        parameter_raster=parameter_raster,
        fdr_raster=d8_fdr,
        out_of_bounds_value=-1,
    )

    # add any pour point accumulation via utilities.adjust_parameter_raster()
    if upstream_pour_points is not None: parameter_raster = adjust_parameter_raster(
        parameter_raster,
        d8_fdr,
        upstream_pour_points,
    )

    # prep kwargs to be passed into accumulate_flow()
    if 'kwargs' in kwargs.keys(): kwargs = kwargs['kwargs']

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2:
        raster_bands = _split_bands(parameter_raster)
    else:
        raster_bands = {(0, 0): parameter_raster}

    # create weighted accumulation rasters
    out_dict = {}
    for index_tuple, array in raster_bands.items():
        i, dim_name = index_tuple

        accumulated = accumulate_flow(
            d8_fdr,
            weights=array,
            kwargs=kwargs,
        )

        out_dict[(i, dim_name)] = accumulated

    # re-combine into DataArray
    if len(out_dict.keys()) > 1:
        out_raster =  _combine_split_bands(out_dict)
    else: out_raster = list(out_dict.items())[0][1] 
    out_raster.name = 'accumulate_parameter'

    # save if necessary and remove temp files
    if isinstance(out_path, str): out_path = Path(out_path)
    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input'])

    return out_raster

def distance_to_stream(
    d8_fdr: Raster,
    fac_raster: Raster,
    accum_threshold: int,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Calculates distance each cell is from a stream (as defined by a cell accumulation threshold).

    NOTE: this is a command line wrapper of TauDEM:D8HDistTostrm and replaces tools.dist2stream() from V1 FCPGtools.

    Args:
        d8_fdr: A TauDEM format D8 Flow Direction Raster (dtype=Int).
        fac_raster: A Flow Accumulation Cell (FAC) raster output from accumulate_flow().
        accum_threshold: The # of upstream/accumulated cells to consider a cell a stream.
        out_path: Defines a path to save the output raster.
        **kwargs: Can pass in optional TauDEM:D8HDistTostrm parameter values using "cores", "mpiCall", or "mpiArg" as keys.

    Returns:
        A raster with values of D8 flow distance from each cell to the nearest stream.
    """
    d8_fdr = _taudem_prepper(d8_fdr)

    # get stream grid as a taudem tempfile
    fac_raster = load_raster(fac_raster)
    fac_raster = fac_raster.fillna(0)
    fac_raster = fac_raster.rio.write_nodata(0)
    fac_raster = fac_raster.astype('int')
    fac_path = _taudem_prepper(fac_raster)

    if out_path is None:
        out_path = Path(
            tempfile.TemporaryFile(
                dir=Path.cwd(),
                prefix='distance_to_stream_temp',
                suffix='.tif',
            ).name
        )
    elif isinstance(out_path, str): out_path = Path(out_path)

    taudem_dict = {
        'fdr': d8_fdr,
        'fac': fac_path,
        'outRast': str(out_path),
        'thresh': accum_threshold,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
    }
    
    taudem_dict = _update_taudem_dict(
        taudem_dict,
        kwargs,
    )

    cmd = '{mpiCall} {mpiArg} {cores} D8HDistTostrm -p {fdr} -src {fac} -dist {outRast} -thresh {thresh}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['outRast']).exists():
        raise FileNotFoundError('TauDEM D8HDistTostrm failed to create an output!')    

    # update nodata values
    out_raster = load_raster(out_path)
    out_raster = change_nodata_value(
        out_raster,
        np.nan,
    )

    # convert 0.1 (minimum) values to np.nan and convert streams to 0
    out_raster = value_mask(
        out_raster,
        thresh=0.1,
    )
    streams = mask_streams(
        fac_raster,
        accum_threshold,
    )
    out_raster = out_raster.where(
        (np.isnan(streams.values)),
        0,
    )

    # clear temporary files and return the output
    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'distance_to_stream_temp'])

    return out_raster

def _ext_upslope_cmd(
    d8_fdr_path: str,
    parameter_raster: xr.DataArray,
    accum_type_str: str,
    **kwargs,
) -> xr.DataArray:
    """Back end function that makes the command line call for TauDEM:D8FlowPathExtremeUp"""

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
        'accum_type': accum_type_str,
        'cores': 1,
        'mpiCall': 'mpiexec',
        'mpiArg': '-n',
    }
    
    taudem_dict = _update_taudem_dict(taudem_dict, kwargs)

    cmd = '{mpiCall} {mpiArg} {cores} D8FlowPathExtremeUp -p {fdr} -sa {param} -ssa {outRast} {accum_type} -nc'.format(
        **taudem_dict)  # Create string of tauDEM shell command
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['outRast']).exists():
        raise FileNotFoundError('TauDEM D8FlowPathExtremeUp failed to create an output!')

    out_raster = load_raster(Path(taudem_dict['outRast']))

    # update nodata and convert -9999 values to nodata
    out_raster = out_raster.where(
        (out_raster != -9999),
        out_raster.rio.nodata,
    )
    out_raster = change_nodata_value(
        out_raster,
        np.nan,
    )

    out_raster.close()
    _clear_temp_files(prefixs=['ext_upslope_temp'])
    return out_raster

def extreme_upslope_values(
    d8_fdr: Raster,
    parameter_raster: Raster,
    mask_streams: Optional[Raster] = None,
    out_path: Optional[Union[str, Path]] = None,
    get_min_upslope: bool = False,
    **kwargs,
) -> xr.DataArray:
    """Finds the max (or min if get_min_upslope=True) value of a parameter grid upstream from each cell in a D8 FDR raster.

    NOTE: This is a wrapper for the TauDEM:d8flowpathextremeup and replaces tools.ExtremeUpslopeValue() from V1 FCPGtools.

    Args:
        d8_fdr: A flow direction raster in TauDEM format.
        parameter_raster: A parameter raster to find the max values from.
        mask_streams: A stream mask raster from tools.mask_streams(). If provided, the output will be masked to only stream cells.
        out_path: Defines a path to save the output raster.
        get_min_upslope: If True, the minimum upslope value is assigned to each cell.
        **kwargs: Can pass in optional TauDEM:d8flowpathextremeup parameter values using "cores", "mpiCall", or "mpiArg" as keys.

    Returns: A raster with max (or min) upstream value of the parameter grid as each cell's value.
    """
    d8_fdr = _taudem_prepper(d8_fdr)
    parameter_raster = load_raster(parameter_raster)
    accum_type_str = '-min' if get_min_upslope else ''

    # prep kwargs to be passed into accumulate_flow()
    if 'kwargs' in kwargs.keys(): kwargs = kwargs['kwargs']

    # split if multi-dimensional
    if len(parameter_raster.shape) > 2: raster_bands = _split_bands(parameter_raster)
    else: raster_bands = {(0, 0): parameter_raster}

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
    if mask_streams is not None:
        if _verify_alignment(out_raster, mask_streams):
            out_raster = out_raster.where(
                (mask_streams != mask_streams.rio.nodata),
                np.nan,
            )
        else: print('WARNING: Stream mask does not align with extream upslope value output! '
            'No mask is applied.'
        )
    
    # update nodata values
    out_raster = change_nodata_value(
        out_raster,
        np.nan,
    )

    # save if necessary
    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'ext_upslope_temp'])
    return out_raster

def _decay_accumulation_cmd(
    dinf_fdr_path: str,
    decay_raster_path: str,
    weights: Optional[xr.DataArray] = None,
    **kwargs,
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

    taudem_dict = _update_taudem_dict(
        taudem_dict,
        kwargs,
    )

    # use TauDEM via subprocess to make a decay accumulation raster
    cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {dinf_fdr_path} -dm {dm} -dsca {dsca} {finalArg}'.format(
        **taudem_dict)
    _ = subprocess.run(cmd, shell=True)

    if not Path(taudem_dict['dsca']).exists():
        raise FileNotFoundError('TauDEM dinfdecayaccum failed to create an output!')

    out_raster = load_raster(Path(taudem_dict['dsca']))

    # update nodata and convert -9999 values to nodata
    out_raster = out_raster.where(
        (out_raster != -9999),
        out_raster.rio.nodata,
    )
    out_raster = change_nodata_value(
        out_raster,
        np.nan,
    )

    out_raster.close()
    _clear_temp_files(prefixs=['decay_accum_temp'])
    return out_raster

def decay_accumulation(
    d8_fdr: Raster,
    decay_raster: Raster,
    upstream_pour_points: Optional[PourPointValuesDict] = None,
    parameter_raster: Optional[Raster] = None,
    out_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> xr.DataArray:
    """Creates a D-Infinity based accumulation raster (parameter or cell accumulation) while applying decay via a multiplier_raster.
    
    NOTE: This is a command line wrapper of TauDEM:DinfDecayAccum and replaces tools.decayAccum() from V1 FCPGtools.

    Args:
        dinf_fdr: A flow direction raster in D-Infinity format. This input can be made with tools.d8_to_dinfinity().
        decay_raster: A decay 'multiplier' raster calculated from distance to stream via tools.make_decay_raster().
        upstream_pour_points: A list of lists each with with coordinate tuples as the first item [0],
            and updated cell values as the second [1].
            This allows the FAC to be made with boundary conditions such as upstream basin pour points.
        parameter_raster: A parameter raster aligned via tools.align_raster() with the us_fdr. 
            This can be multi-dimensional (i.e. f(x, y, t)), and if so, a multi-dimensional output is returned.
        out_path: Defines a path to save the output raster.
        **kwargs: Can pass in optional TauDEM:DinfDecayAccum parameter values using "cores", "mpiCall", or "mpiArg" as keys.

    Returns:
        The output decayed accumulation raster.
    """
    # prep data for taudem
    d8_fdr = load_raster(d8_fdr)
    dinf_fdr = d8_to_dinfinity(d8_fdr)
    
    dinf_fdr_path = _taudem_prepper(dinf_fdr)
    decay_raster_path = _taudem_prepper(decay_raster)

    # prep kwargs to be passed into accumulate_flow()
    if 'kwargs' in kwargs.keys(): kwargs = kwargs['kwargs']

    # prep parameter raster and boundary conditions
    weights = None
    if parameter_raster is not None: weights = load_raster(parameter_raster)
    elif upstream_pour_points is not None:
        weights = xr.zeros_like(
            dinf_fdr,
            dtype=np.dtype('float64'),
        ) + 1
    if weights is not None:
        if upstream_pour_points is not None:
            weights = adjust_parameter_raster(
                weights,
                d8_fdr,
                upstream_pour_points,
            )
        weights = make_fac_weights(
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
    out_raster = make_fac_weights(
        out_raster,
        d8_fdr,
        np.nan,
    )
    out_raster = change_nodata_value(
        out_raster,
        np.nan,
    )

    # save if necessary
    if out_path is not None:
        save_raster(
            out_raster,
            out_path,
        )

    out_raster.close()
    _clear_temp_files(prefixs=['taudem_temp_input', 'decay_accum_temp'])
    return out_raster



