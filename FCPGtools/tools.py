import rasterio as rs
import numpy as np
import sys
import os
import pandas as pd
import subprocess
import glob
import shutil
import traceback
import datetime
from multiprocessing import Pool as processPool

# Imports for reading and writing json files
import json
import io

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

# Imports for cascade tools
from rasterio.mask import mask
import matplotlib.pyplot as plt
import geopandas as gpd

def parsebool(b):
    '''Parse a boolean argument from the command line.

    Parameters
    ----------
    b : str
        String of either True or False.

    Returns
    -------
    res : bool
        True if b is "True" or False if b is not "True."

    '''

    return b == "True"

def tauDrainDir(inRast, outRast, band = 1, updateDict = {
            'compress':'LZW',
            'zlevel':9,
            'interleave':'band',
            'sparse':True,
            'tiled':True,
            'blockysize':256,
            'blockxsize':256,
            'driver' : "GTiff",
            'nodata':0,
            'bigtiff':'IF_SAFER'}, verbose = False):
    """Reclassifies ESRI flow directions into TauDEM flow directions.

    Parameters
    ----------
    inRast : str
        Path to a raster encoded with ESRI flow direction values.
    outRast : str
        Path to output a raster with flow directions encoded for TauDEM. File will be overwritten if it already exists.
    band : int (optional)
        Band to read the flow direction grid from if inRast is multiband, defaults to 1.
    updateDict : dict (optional)
        Dictionary of Rasterio raster options used to create outRast. Defaults have been supplied, but may not work in all situations and input file formats.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster
        Reclassified flow direction raster at the path specified above.
    """
    assert os.path.isfile(inRast)==True, 'inRast not found'

    if verbose: print('Reclassifying Flow Directions...')

    # load input data
    with rs.open(inRast) as ds:
        assert ds.meta['count'] <= band, 'inRast missing specified band'
        dat = ds.read(band)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

    tauDir = dat.copy()
    # remap NHDplus flow direction to TauDEM flow Direction
    # east is ok
    
    tauDir[dat == 2] = 8 # southeast
    tauDir[dat == 4] = 7 # south
    tauDir[dat == 8] = 6 # southwest
    tauDir[dat == 16] = 5 # west
    tauDir[dat == 32] = 4 # northwest
    tauDir[dat == 64] = 3 # north
    tauDir[dat == 128] = 2 # northeast
    tauDir[dat == inNoData] = 0 # no data
    tauDir = tauDir.astype('uint8')#8 bit integer is sufficient for flow directions

    # edit the metadata
    profile.update(updateDict)
    
    if os.path.isfile(outRast):
    	os.remove(outRast)

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(tauDir,1)
        if verbose: print("TauDEM drainage direction written to: {0}".format(outRast))

def accumulateParam(paramRast, fdr, accumRast, outNoDataRast = None, outNoDataAccum = None, zeroNoDataRast = None, cores = 1, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False):
    """Accumulate a parameter grid using TauDEM AreaD8 :cite:`TauDEM`.

    Parameters
    ----------
    paramRast : str 
        Raster of parameter values to accumulate; this file is modified by the function.
    fdr : str
        Flow direction raster in TauDEM format.
    accumRast : str
        File location to store accumulated parameter values.
    outNoDataRast : str (optional)
        File location to store parameter no data raster.
    outNoDataAccum : str (optional)
        File location to store accumulated no data raster.
    zeroNoDataRast : str (optional)
        File location to store the no data raster filled with zeros.
    cores : int (optional)
        The number of cores to use for parameter accumulation. Defaults to 1.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter.
    verbose : bool (optional)
        Print output, defaults to False.


    Returns
    -------
    accumRast : raster
        Raster of accumulated parameter values.
    outNoDataRast : raster
        Raster of no data values.
    outNoDataRast : raster
        Raster of accumulated no data values.

    Notes
    -----
	If outNoDataRast, outNoDataAccum, and zeroNoDataRast inputs are all supplied it will set any “no data” values in the basin to zero and save that raster as zeroNoDataRast. It will then save a raster with all no data values set to one and other values set to zero (outNoDataRast) and use tauDEM to accumulate it (outNoDataAccum). It will then accumulate the parameter from the zeroNoDataRast, and a subsequent correction will be needed in the make_fcpg() function based on the values in the outNoDataAccum raster. 

	If some of the output file locations for handling no data values aren’t supplied or “no data” values aren’t present in the parameter grid, it will simply accumulate the parameter grid. If “no data” values are present, this will result in them being propagated downstream. 

    """

    if not os.path.isfile(paramRast):
        print("Error - Parameter raster file is missing!")
        return #Function will fail, so end it now
    if not os.path.isfile(fdr):
        print("Error - Flow direction file is missing!")
        return #Function will fail, so end it now

    with rs.open(paramRast) as ds: # load parameter raster
        data = ds.read(1)
        profile = ds.profile
        paramNoData = ds.nodata

    with rs.open(fdr) as ds: # load flow direction raster
        direction = ds.read(1)
        directionNoData = ds.nodata # pull the accumulated area no data value

    if paramNoData == None:
        print("Warning: Parameter raster no data value not specified, results may be invalid")


    #Deal with no data values
    basinNoDataCount = len(data[(data == paramNoData) & (direction != directionNoData)]) # Count number of cells with flow direction but no parameter value
    
    if basinNoDataCount > 0:
        print('Warning: No data parameter values exist in basin')


        #If a no data file path is given, accumulate no data values
        if (outNoDataRast != None) & (outNoDataAccum != None) & (zeroNoDataRast != None):

            #Set no data parameter values in the basin to zero so tauDEM accumulates them
            noDataZero = data.copy()
            noDataZero[(data == paramNoData) & (direction != directionNoData)] = 0 #Set no data values in basin to 0

            # Update profile for no data raster
            newProfile = profile 
            newProfile.update({
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'bigtiff':'IF_SAFER'})
            
            # Save no data raster
            with rs.open(zeroNoDataRast, 'w', **newProfile) as dst:
                dst.write(noDataZero,1)
                if verbose: print("Parameter Zero No Data raster written to: {0}".format(zeroNoDataRast))


            
            noDataArray = data.copy()
            noDataArray[(data == paramNoData) & (direction != directionNoData)] = 1 #Set no data values in basin to 1
            noDataArray[(data != paramNoData)] = 0 #Set values with data to 0
            noDataArray[(direction == directionNoData)] = -1 #Set all values outside of basin to -1
            noDataArray = noDataArray.astype(np.int8)

            # Update profile for no data raster
            newProfile = profile 
            newProfile.update({
                    'dtype':'int8',
                    'compress':'LZW',
                    'zlevel':9,
                    'interleave':'band',
                    'profile':'GeoTIFF',
                    'tiled':True,
                    'sparse_ok':True,
                    'num_threads':'ALL_CPUS',
                    'nodata':-1,
                    'bigtiff':'IF_SAFER'})
            
            # Save no data raster
            with rs.open(outNoDataRast, 'w', **newProfile) as dst:
                dst.write(noDataArray,1)
                if verbose: print("Parameter No Data raster written to: {0}".format(outNoDataRast))


            # Use tauDEM to accumulate no data values
            try:
                if verbose: print('Accumulating No Data Values')
                
                    
                tauParams = {
                'fdr':fdr,
                'cores':cores, 
                'outFl':outNoDataAccum,
                'weight':outNoDataRast,
                'mpiCall':mpiCall,
                'mpiArg':mpiArg
                }
                
                cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
                if verbose: print(cmd)
                result = subprocess.run(cmd, shell = True) # Run shell command
                result.stdout
                if verbose: print("Parameter no data accumulation written to: {0}".format(outNoDataRast))
                
            except:
                print('Error Accumulating Data')
                traceback.print_exc()

            tauDEMweight = zeroNoDataRast #Set file to use as weight in tauDEM accumulation

        else:
            #If some of the no data handling files aren't provided, accumulate the parameter with no data values included
            #This will result in no data values being propagated downstream
            tauDEMweight = paramRast #Set file to use as weight in tauDEM accumulation
        

            
    else:

        #If there are zero no data values in the basin, simply accumulate the parameter raster
        tauDEMweight = paramRast #Set file to use as weight in tauDEM accumulation

            

    #Use tauDEM to accumulate the parameter
    try:
        if verbose: print('Accumulating Data...')
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'outFl':accumRast, 
        'weight':tauDEMweight,
        'mpiCall':mpiCall,
        'mpiArg':mpiArg
        }
        
        cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
        if verbose: print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        

    except:
        print('Error Accumulating Data')
        traceback.print_exc()

    
def make_fcpg(accumParam, fac, outRast, noDataRast = None, minAccum = None, verbose = False):
    '''Create a flow-conditioned parameter grid using accumulated parameter and area rasters. See also :py:func:`make_fcpgs`.

    Parameters
    ----------
    accumParam : str
        File location of the accumulated parameter data raster.
    fac : str
        File location of the flow accumulation raster.
    outRast : str
        File location of the output flow-conditioned parameter grid.
    noDataRast : str
        File location of the accumulated parameter no data raster.
    minAccum : float
        Value of flow accumulation below which the CPG values will be set to no data.
    verbose : bool (optional)
        Print output, defaults to False.
        
    Returns
    -------
    outRast : raster
        Flow-conditioned parameter grid file where grid cell values represent the mean upstream value of the paramter. 
    '''
    outNoData = -9999
    

    if not os.path.isfile(accumParam):
        print("Error - Accumulated parameter raster file is missing!")
        return #Function will fail, so end it now
    if not os.path.isfile(fac):
        print("Error - Flow accumulation file is missing!")
        return #Function will fail, so end it now


    if verbose: print("Reading accumulated parameter file {0}".format(datetime.datetime.now()))
    with rs.open(accumParam) as ds: # load accumulated data and no data rasters
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata

    data = data.astype(np.float32) #Convert to 32 bit float
    data[data == inNoData] = np.NaN # fill with no data values where appropriate

    if verbose: print("Reading basin flow accumulation file {0}".format(datetime.datetime.now()))
    with rs.open(fac) as ds: # flow accumulation raster
        accum = ds.read(1)
        facNoData = ds.nodata # pull the accumulated area no data value


    if noDataRast != None:
        if verbose: print("Correcting CPG for no data values")
        with rs.open(noDataRast) as ds: # accumulated no data raster
            accumNoData = ds.read(1)
            noDataNoData = ds.nodata # pull the accumulated no data no data value
            
        accumNoData[accumNoData == noDataNoData] = 0 #Set no data values to zero

        corrAccum = accum - accumNoData # Compute corrected accumulation
        corrAccum = corrAccum.astype(np.float32) # Convert to 32 bit float
        corrAccum[accum == facNoData] = np.NaN # fill with no data values where appropriate
        
    else:
        accum2 = accum.astype(np.float32)
        accum2[accum == facNoData] = np.NaN # fill this with no data values where appropriate
        corrAccum = accum2 # No correction required
        
    # Throw warning if there is a negative accumulation
    if np.nanmin(corrAccum) < 0:
        print("Warning: Negative accumulation value")
        print("Minimum value:{0}".format(np.nanmin(corrAccum)))
 
    if verbose: print("Computing CPG values {0}".format(datetime.datetime.now()))
    dataCPG = data / (corrAccum + 1) # make data CPG

    if verbose: print("Replacing numpy nan values {0}".format(datetime.datetime.now()))
    dataCPG[np.isnan(dataCPG)] = outNoData # Replace numpy NaNs with no data value

    # Replace values in cells with small flow accumulation with no data
    if minAccum != None:
        if verbose: print("Replacing small flow accumulations {0}".format(datetime.datetime.now()))
        dataCPG[corrAccum < minAccum] = outNoData #Set values smaller than threshold to no data

    # Update raster profile
    profile.update({'dtype':dataCPG.dtype,
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'bigtiff':'IF_SAFER'})

    if verbose: print("Saving CPG raster {0}".format(datetime.datetime.now()))
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(dataCPG,1)
        if verbose: print("CPG file written to: {0}".format(outRast))
    
def resampleParam(inParam, fdr, outParam, resampleMethod="bilinear", cores=1, forceProj=False, forceProj4="\"+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs\"", verbose = False):
    '''Resample, re-project, and clip the parameter raster based on the resolution, projection, and extent of the of the flow direction raster supplied. See also :py:func:`resampleParams`.

    Parameters
    ----------
    inParam : str
        Path to the input parameter data raster
    fdr : str
        Path to the flow direction raster
    outParam : str
        Path to the output file for the resampled parameter raster.
    resampleMethod : str (optional)
        resampling method, either 'bilinear' or 'nearest neighbor'. Bilinear should generally be used for continuous data sets such as precipitation while nearest neighbor should generally be used for categorical datasets such as land cover type. Defaults to bilinear.
    cores : int (optional)
        The number of cores to use. Defaults to 1.
    forceProj : bool (optional)
        Force the projection of the flow direction raster. This can be useful if the flow direction raster has an unusual projection. Defaults to False. This parameter defaults to False; however, if set to True, forceProj4 must also be specified or the default proj4 string for USGS Albers will be used, see below.
    forceProj4 : str (optional)
        Proj4 string used to force the flow direction raster. This defaults to USGS Albers, but is not used unless the forceProj parameter is set to True.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outParam : raster
        Resampled, reprojected, and clipped parameter raster.
    '''

    with rs.open(fdr) as ds: # load flow direction raster in Rasterio
        fdrcrs = ds.crs #Get flow direction coordinate system
        xsize, ysize = ds.res #Get flow direction cell size
        #Get bounding coordinates of the flow direction raster
        fdrXmin = ds.transform[2]
        fdrYmax = ds.transform[5]
        fdrXmax = fdrXmin + xsize*ds.width
        fdrYmin = fdrYmax - ysize*ds.height

    with rs.open(inParam) as ds: # load parameter raster in Rasterio
        paramNoData = ds.nodata
        paramType = ds.dtypes[0] #Get datatype of first band
        paramcrs = ds.crs #Get parameter coordinate reference system
        paramXsize, paramYsize = ds.res #Get parameter cell size

    # override the FDR projection if specified.
    if forceProj:
        fdrcrs = forceProj4

    if verbose: print("Flow Direction Proj4: " + str(fdrcrs))
    if verbose: print("Parameter Proj4:" + str(paramcrs))

    if verbose: print("Flow Direction Xsize:" + str(xsize))
    if verbose: print("Parameter Xsize:" + str(paramXsize))
    
    # Choose an appropriate gdal data type for the parameter
    if paramType == 'int8':
        outType = 'Byte' # Use Gdal convention #old# Convert 8 bit integers to 16 bit in gdal
        #print("Warning: 8 bit inputs are unsupported and may not be reprojected correctly") #Print warning that gdal may cause problems with 8 bit rasters
    elif paramType == 'int16':
        outType = 'Int16' 
    elif paramType == 'int32':
        outType = 'Int32'
    elif paramType == 'int64':
        outType = 'Int64'
    elif paramType == 'float32':
        outType = 'Float32'
    elif paramType == 'float64':
        outType = 'Float64'
    else:
        print("Warning: Unsupported data type {0}".format(paramType))
        print("Defaulting to Float64")
        outType = 'Float64' # Try a 64 bit floating point if all else fails

    #Check if resampling or reprojection are required
    if str(paramcrs) == str(fdrcrs) and paramXsize == xsize and paramYsize == ysize:
        if verbose: print("Parameter does not require reprojection or resampling")
    
    else:

        # Resample, reproject, and clip the parameter raster with GDAL
        try:
            if verbose: print('Resampling and Reprojecting Parameter Raster...')
            warpParams = {
            'inParam': inParam,
            'outParam': outParam,
            'fdr':fdr,
            'cores':str(cores), 
            'resampleMethod': resampleMethod,
            'xsize': xsize, 
            'ysize': ysize, 
            'fdrXmin': fdrXmin,
            'fdrXmax': fdrXmax,
            'fdrYmin': fdrYmin,
            'fdrYmax': fdrYmax,
            'fdrcrs': fdrcrs, 
            'nodata': paramNoData,
            'datatype': outType
            }
            
            cmd = 'gdalwarp -overwrite -tr {xsize} {ysize} -t_srs {fdrcrs} -te {fdrXmin} {fdrYmin} {fdrXmax} {fdrYmax} -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "ZLEVEL=9" -co "NUM_THREADS={cores}" -co "BIGTIFF=IF_SAFER" -r {resampleMethod} -dstnodata {nodata} -ot {datatype} {inParam} {outParam}'.format(**warpParams)
            if verbose: print(cmd)
            result = subprocess.run(cmd, shell = True)
            result.stdout
            
        except:
            print('Error Reprojecting Parameter Raster')
            traceback.print_exc()

#Tools for decayed accumulation CPGs

def makeDecayGrid(d2strm, k, outRast, verbose = False):
    '''Create a decay raster where grid cell values are computed as the inverse number of grid cells, :math:`\\frac{dx}{n+k*dx}`, where n is the distance from the d2strm raster from each grid cell to the nearest stream, k is a constant applied to the cell size values, and dx is the cell size of the raster.
    
    Parameters
    ----------
    d2strm : str
        Path to raster of flow distances from each grid cell to the nearest stream.
    k : float
        Dimensionless constant applied to decay factor denominator. Must be less than 1 for decay to occur along streamlines. 
    outRast : str
        Output file path for decay grid.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
        outRast : raster
            Raster file with grid cells values representing weights decaying as a function of the distance to stream.
    '''
    if not os.path.isfile(d2strm):
        print("Error - Stream distance raster file is missing!")
        return #Function will fail, so end it now


    with rs.open(d2strm) as ds: # load flow direction data
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata
        xsize, ysize = ds.res #Get flow direction cell size
    
    if xsize != ysize:
        print("Warning - grid cells are not square, results may be incorrect")


    outNoData = 0 #Set no data value for output raster

    if verbose: print("Building decay grid {0}".format(datetime.datetime.now()))
    decayGrid = data.astype(np.float32) #Convert to float
    decayGrid[data == inNoData] = np.NaN # fill with no data values where appropriate
    decayGrid = xsize/(decayGrid + k*xsize) #Compute decay function

    decayGrid[np.isnan(decayGrid)] = outNoData # Replace numpy NaNs with no data value

    # Update raster profile
    profile.update({
                'dtype': decayGrid.dtype,
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':inNoData,
                'bigtiff':'IF_SAFER'})

    if verbose: print("Saving decay raster {0}".format(datetime.datetime.now()))
    
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(decayGrid,1)
        if verbose: print("Decay raster written to: {0}".format(outRast))

def applyMult(inRast, mult, outRast, verbose = False):
    '''Multiply input raster by mult.

    Parameters
    ----------
    inRast : str
        Path to input raster.
    mult : str
        Path to multiplier raster.
    outRast : str
        Path to output raster.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster
        Input raster multiplied by the multiplier raster.
    '''  

    if not os.path.isfile(inRast):
        print("Error - Input parameter raster file is missing!")
        return #Function will fail, so end it now

    if not os.path.isfile(mult):
        print("Error - Multiplier file is missing!")
        return #Function will fail, so end it now


    if verbose: print("Reading input rasters {0}".format(datetime.datetime.now()))
    with rs.open(inRast) as ds: # load input rasters
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata
    
    with rs.open(mult) as ds: # load input rasters
        m = ds.read(1)
        mNoData = ds.nodata

    data = data.astype(np.float32) #Convert to 32 bit float
    data[data == inNoData] = np.NaN # fill with no data values where appropriate
    m[m == mNoData] = np.NaN # fill with no data values where appropriate
    outData = data * mult #Multiply the parameter values by the multiplier

    outNoData = -9999
    outData[np.isnan(outData)] = outNoData # Replace numpy NaNs with no data value

    # Update raster profile
    profile.update({'dtype':outData.dtype,
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'bigtiff':'IF_SAFER'})

    if verbose: print("Saving raster {0}".format(datetime.datetime.now()))
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(outData,1)
        if verbose: print("Raster written to: {0}".format(outRast))


def decayAccum(ang, mult, outRast, paramRast = None, cores=1, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False) :
    '''Decay the accumulation of a parameter raster.

    Parameters
    ----------
    ang : str
        Path to flow angle raster from the TauDEM D-Infinity flow direction tool.
    mult : str
        Path to raster of multiplier values applied to upstream accumulations, 1 corresponds to no decay, 0 corresponds to complete decay.
    outRast : str
        Path to output raster for decayed accumulation raster.
    paramRast : str (optional)
        Raster of parameter values to accumulate. If not supplied area will be accumulated. Defaults to None.
    cores : int (optional)
        Number of cores to use. Defaults to 1.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster
        Decayed accumulation raster, either area or parameter depending on what is supplied to the function.
    '''

    if paramRast != None:
        try:
            if verbose: print('Accumulating parameter')
            tauParams = {
            'ang':ang,
            'cores':cores, 
            'dm':mult,
            'dsca': outRast,
            'weight':paramRast,
            'mpiCall':mpiCall,
            'mpiArg':mpiArg
            }
                    
            cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
            if verbose: print(cmd)
            result = subprocess.run(cmd, shell = True) # Run shell command
            result.stdout
            if verbose: print("Parameter accumulation written to: {0}".format(outRast))
                    
        except:
            print('Error Accumulating Data')
            traceback.print_exc()
    else:
        try:
            if verbose: print('Accumulating parameter')
            tauParams = {
            'ang':ang,
            'cores':cores, 
            'dm':mult,
            'dsca': outRast,
            'mpiCall':mpiCall,
            'mpiArg':mpiArg
            }
                    
            cmd = '{mpiCall} {mpiArg} {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -nc'.format(**tauParams) # Create string of tauDEM shell command
            if verbose: print(cmd)
            result = subprocess.run(cmd, shell = True) # Run shell command
            result.stdout
            if verbose: print("Parameter accumulation written to: {0}".format(outRast))
                
        except:
            print('Error Accumulating Data')
            traceback.print_exc()



def dist2stream(fdr, fac, thresh, outRast, cores=1, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False) :
    '''Compute distance to streams.
    
    Parameters
    ----------
    fdr : str
        Path to flow direction raster in TauDEM format.
    fac : str
        Path to flow accumulation raster.
    thresh : int
        Accumulation threshold for stream formation in number of grid cells.
    outRast : str
        Path to output the distance raster.
    cores : int (optional)
        The number of cores to use. Defaults to 1.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster 
        Raster with values of D-8 flow distance from each cell to the nearest stream.
    '''

    try:
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'fac':fac,
        'outRast': outRast,
        'thresh':thresh,
        'mpiCall':mpiCall,
        'mpiArg':mpiArg
        }
                
        cmd = '{mpiCall} {mpiArg} {cores} d8hdisttostrm -p {fdr} -src {fac} -dist {outRast}, -thresh {thresh}'.format(**tauParams) # Create string of tauDEM shell command
        if verbose: print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout
        if verbose: print("Distance raster written to: {0}".format(outRast))
                
    except:
        print('Error computing distances')
        traceback.print_exc()

def maskStreams(inRast, streamRast, outRast, verbose = False):
    '''Mask areas not on the stream network.

    Parameters
    ----------
    inRast : str
        Path to the input raster to mask.
    streamRast : str
        Path to the stream raster where all non-stream cells are set to no data.
    outRast : str
        Path to output raster file.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : raster
        Raster with non-stream cells set to the no data value from inRast.
    '''
  
    if not os.path.isfile(inRast):
        print("Error - Parameter raster file is missing!")
        return #Function will fail, so end it now
    if not os.path.isfile(streamRast):
        print("Error - Stream raster file is missing!")
        return #Function will fail, so end it now


    with rs.open(inRast) as ds: # load input raster
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata 

    with rs.open(streamRast) as ds: # load input raster
        strmVals = ds.read(1)
        strmNoData = ds.nodata 

    data[data == inNoData] = np.NaN #Set no data values to NaN
    data[strmVals == strmNoData] = np.NaN #Set values off streams to NaN

    data[data == np.NaN] = inNoData #Set NaNs to input no data value

    # Update raster profile
    profile.update({
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':inNoData,
                'bigtiff':'IF_SAFER'})

    if verbose: print("Saving raster {0}".format(datetime.datetime.now()))
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(data,1)
        if verbose: print("CPG file written to: {0}".format(outRast))

def resampleParam_batch(inParams, fdr, outWorkspace, resampleMethod="bilinear", cores=1, appStr="rprj", forceProj=False, forceProj4="\"+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs\"", verbose = False):
    '''Batch version of :py:func:`resampleParam`.

    Parameters
    ----------
    inParam : list
        List of input parameter raster paths.
    fdr : str
        Path to the flow direction raster.
    outWorkspace :  
        Path to the output directory for the resampled rasters.
    resampleMethod : str (optional)
        Resampling method, either bilinear or nearest neighbor. Defaults to bilinear.
    cores :
        Number of cores to use. Defaults to 1.
    appStr : str (optional)
        String of text to append to the input parameter filenames. Defaults to "rprj."
    forceProj : bool (optional)
        Force the projection of the flow direction raster. This can be useful if the flow direction raster has an unusual projection. Defaults to False.
    forceProj4 : str (optional)
        Proj4 string used to force the flow direction raster. This defaults to USGS Albers, but is not used unless the forceProj parameter is set to True.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    fileList : list
        Paths to resampled, reprojected, and clipped parameter rasters.
    '''

    fileList = [] #Initialize list of output files

    for param in inParams:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention

        
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        resampleParam(param, fdr, outPath, resampleMethod, cores, forceProj=forceProj, forceProj4=forceProj4, verbose = verbose) #Run the resample function for the parameter raster

    return fileList

def accumulateParam_batch(paramRasts, fdr, outWorkspace, cores = 1, appStr="accum", mpiCall = 'mpiexec', mpiArg = '-n', verbose = False):
    '''Batch version of :py:func:`accumulateParam`.

    Parameters
    ----------
    paramRasts : list
        List of input parameter raster paths to accumulate along the supplied fdr.
    fdr : str
        Path to the flow direction raster.
    outWorkspace : str
        Path to the output directory for accumulation rasters.
    cores : int (optional)
        Number of cores to use. Defaults to 1.
    appStr :str (optional)
        String of text to append to accumulated parameter filenames. Defaults to "accum."
    mpiCall : str (optional)
        MPI program to use to execute the program, defaults to mpiexec.
    mpiArg : str (optional)
        Argument to pass to mpiCall, defaults to -n.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    fileList : list
        List of file paths to accumulated parameter rasters.
    '''

    fileList = [] #Initialize list of output files
    
    for param in paramRasts:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        nodataPath = os.path.join(outWorkspace, baseName + "nodata" + ext) 
        nodataAccumPath = os.path.join(outWorkspace, baseName + "nodataaccum" + ext) 

        accumulateParam(param, fdr, outPath, outNoDataRast=nodataPath, outNoDataAccum=nodataAccumPath, cores=cores, mpiCall = mpiCall, mpiArg = mpiArg) #Run the flow accumulation function for the parameter raster

    return fileList

def make_fcpg_batch(accumParams, fac, outWorkspace, minAccum=None, appStr="FCPG", verbose = False):
    '''Batch version of :py:func:`make_fcpg`.

    Parameters
    ----------
    accumParams : list
        List of accumulated parameter rasters to create FCPGs from.
    fac : str
        Path to the flow accumulation raster.
    outWorkspace : str
        Path to an output directory for produced FCPGs.
    minAccum : int (optional)
        Minimum accumulation value below which the output FCPG will be turned to no data values. Defaults to None.
    appStr : str (optional)
        String of text to append to filenames of the produced FCPG grids.
    verbose : bool (optional)
        Print output, defaults to False.
    
    Returns
    -------
    fileList : list
        List of file paths to the produced FCPGs.
    '''

    fileList = [] #Initialize list of output files

    for param in accumParams:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        make_fcpg(param, fac, outPath, minAccum=minAccum, verbose = verbose) #Run the CPG function for the accumulated parameter raster

    return fileList

def cat2bin(inCat, outWorkspace, par=True, verbose = False):
    '''Turn a categorical raster (e.g. land cover type) into a set of binary rasters, one for each category in the supplied raster, zero for areas where that class is not present, 1 for areas where that class is present, and -1 for regions of no data in the supplied raster. Wrapper on :py:func:`binarizeCat`.

    Parameters
    ----------
    inCat : str
        Input catagorical parameter raster.
    outWorkspace : str
        Workspace to save binary raster output files.
    par : bool (optional)
        Use parallel processing to generate binary rasters, defaults to True.
    verbose : bool (optional)
        Print output, defaults to False.
        
    Returns
    -------
    fileList : list
        List of filepaths to output files.
    '''
    if verbose: print("Creating binaries for %s"%inCat)
    
    baseName = os.path.splitext(os.path.basename(inCat))[0] #Get name of input file without extention
    

    # load input data
    with rs.open(inCat) as ds:
        dat = ds.read(1)
        profile = ds.profile.copy() # save the metadata for output later
        nodata = ds.nodata
    
    cats = np.unique(dat) # Get unique values in raster
    cats = np.delete(cats, np.where(cats ==  nodata)) # Remove no data value from list

    fileList = [] #Initialize list of output files

    # edit the metadata
    profile.update({'dtype':'int8',
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-1,#Use -1 as no data value
                'bigtiff':'IF_SAFER'})
    
    ext = ".tif" #Output file extension

    #Create binary rasters for each category
    if par:
        from functools import partial
        pool = processPool()

        # Use pool.map() to create binaries in parallel
        fileList = pool.map(partial(binarizeCat, data=dat, nodata=nodata, outWorkspace=outWorkspace, baseName=baseName, ext=ext, profile=profile), cats)

        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
    else:
        fileList = []
        for cat in cats:
            fileList.append(binarizeCat(data = dat, val = cat, nodata = nodata, outWorkspace = outWorkspace, baseName = baseName, ext = ext, profile = profile))
    
    return fileList

def binarizeCat(val, data, nodata, outWorkspace, baseName, ext, profile, verbose = False):
    '''Turn a categorical raster (e.g. land cover type) into a set of binary rasters, one for each category in the supplied raster, zero for areas where that class is not present, 1 for areas where that class is present, and -1 for regions of no data in the supplied raster. See also :py:func:`cat2bin`.

    Parameters
    ----------
    data : np.array
        Numpy array of raster data to convert to binary.
    val : int
        Raster value to extract binary for from data.
    nodata : int or float
        Raster no data value.
    outWorkspace : str
        Path to folder to save binary output rasters to.
    baseName : str
        Base name for the output rasters.
    ext : str
        File extension for output rasters.
    profile : dict
    	Rasterio metadata dictionary decribing the properties used to create the output raster.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    catRaster : str
        Filepath to the binary raster created.
    '''

    catData = data.copy()
    catData[(data != val) & (data != nodata)] = 0
    catData[data == val] = 1
    catData[data == nodata] = -1 #Use -1 as no data value
    catData = catData.astype('int8')#8 bit integer is sufficient for zeros and ones

    catRasterName = baseName + str(val) + ext
    catRaster = os.path.join(outWorkspace, catRasterName)

    if verbose: print("Saving %s"%catRaster)
    with rs.open(catRaster,'w',**profile) as dst:
        dst.write(catData,1)

    return catRaster # Return the path to the raster created

def tauFlowAccum(fdr, accumRast, cores = 1, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False):
    """Wrapper for TauDEM AreaD8 :cite:`TauDEM` to produce a flow acculation grid.

    Parameters
    ----------
    fdr : str
        Path to a flow direction raster in TauDEM format.
    accumRast : str
        Path to output the flow accumulation raster.
    cores : int (optional)
        Number of cores to use. Defaults to 1.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter.
    verbose : bool (optional)
        Print output, defaults to False.


    Returns
    -------
    accumRast : raster
        Raster of accumulated parameter values at the path specified above.
    """
    #Use tauDEM to accumulate the parameter
    try:
        if verbose: print('Accumulating Data...')
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'outFl':accumRast,
        'mpiCall':mpiCall,
        'mpiArg':mpiArg
        }
        
        cmd = '{mpiCall} {mpiArg} {cores} aread8 -p {fdr} -ad8 {outFl} -nc'.format(**tauParams) # Create string of tauDEM shell command
        if verbose: print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        
    except:
        print('Error Accumulating Data')
        traceback.print_exc()

def ExtremeUpslopeValue(fdr, param, output, accum_type = "MAX", cores = 1, fac = None, thresh = None, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False):
    '''
    Wrapper for the TauDEM D8 Extreme Upslope Value function :cite:`TauDEM`.

    Parameters
    ----------
    fdr : str
        Path to a flow direction grid in TauDEM format.
    param : str
        Path to parameter raster to run through the D8 Extreme Upslope Value tool
    output : str
        Path to output raster file.
    accum_type : str (optional) 
        Either  "MAX" or "MIN." Defaults to "MAX."
    cores : int (optional) 
        Number of cores to run this process on. Defaults to 1.
    fac : str (optional)
        Path to a flow accumulation raster. Defaults to None.
    thresh : int (optional)
        Threshold values, in the same units as fac to mask output to stream channels. Defaults to None.
    mpiCall : str (optional)
        The command to use for mpi, defaults to mpiexec.
    mpiArg : str (optional)
        Argument flag passed to mpiCall, which is followed by the cores parameter, defaults to '-n'
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    output : raster
        Raster of either the maximum or minumum upslope value of the parameter grid supplied to the function.
    '''
    

    tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'outFl':output,
        'param':param,
        'accum_type':accum_type.lower(),
        'mpiCall':mpiCall,
        'mpiArg':mpiArg
        }

    if accum_type == "min": # insert flag for min 
        cmd = '{mpiCall} {mpiArg} {cores} d8flowpathextremeup -p {fdr} -sa {param} -ssa {outFl} -{accum_type} -nc'.format(**tauParams) # Create string of tauDEM shell command
    else: # no flag for max
        cmd = '{mpiCall} {mpiArg} {cores} d8flowpathextremeup -p {fdr} -sa {param} -ssa {outFl} -nc'.format(**tauParams) # Create string of tauDEM shell command

    if verbose: print(cmd) # print the command to be run to the output.
    result = subprocess.run(cmd, shell = True) # Run shell command
        
    result.stdout

    if fac != None and thresh != None: # if a stream mask is specified
        outNoData = -9999

        with rs.open(output) as src:
            dat = src.read(1)
            params = src.meta.copy()
            noData = src.nodata
            dat[dat == noData] = np.NaN
            
        del src

        with rs.open(fac) as src:
            fac = src.read(1)
            fac[fac == src.nodata] = outNoData

        del src

        dat[fac < thresh] = outNoData # make low accumulation areas noData
        dat[fac == outNoData] = outNoData # make borders noData

        params['nodata'] = outNoData

        with rs.open(output,'w',**params) as dst: # write out raster.
            dst.write(dat,1)

    return None

def getFeatures(gdf):
    """Helper function to parse features from a GeoPandas GeoDataframe in such a manner that Rasterio can handle them.
    
    Parameters
    ----------
    gdf : GeoDataframe
        GeoPandas GeoDataframe with a geometry column.

    Returns
    -------
    features : geoJSON
        GeoJSON representation of geometry features from the input GeoDataFrame.
    """

    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

def getHUC4(HUC12):
    '''Helper function to return HUC4 representation from a HUC12 identifier.

    Parameters
    ----------
    HUC12 : str
        Text representation of the HUC12 identifier.

    Returns
    -------
    HUC4 : str
        HUC4 identifier.
    '''
    return HUC12[:4]

def makePourBasins(wbd,fromHUC4,toHUC4,HUC12Key = 'HUC12', ToHUCKey = 'ToHUC'):
    '''Make geodataframe of HUC12 basis flowing from fromHUC4 to toHUC4.
    
    Parameters
    ----------
    wbd : GeoDataframe
        HUC12-level geodataframe projected to the same coordinate reference system (CRS) as the flow accumulation (FAC) and flow direction (FDR) grids being used.
    fromHUC4 : str
        HUC4 string for the upstream basin.
    toHUC4 : str
        HUC string for the downstream basin.
    HUC12Key : str (optional)
        Column name for HUC codes to process down to HUC4 codes, defaults to 'HUC12'.
    ToHUCKey : str (optional)
        Column name for the column that indicates the downstream HUC for each row of the dataframe, defaults to 'TOHUC'.
        
    Returns
    -------
    pourBasins : GeoDataframe
        HUC12-level geodataframe of units that drain from fromHUC4 to toHUC4.
    '''
    
    wbd['HUC4'] = wbd[HUC12Key].map(getHUC4)
    wbd['ToHUC4'] = wbd[ToHUCKey].map(getHUC4)
    
    return wbd.loc[(wbd.HUC4 == fromHUC4) & (wbd.ToHUC4 == toHUC4)].copy()

def findPourPoints(pourBasins, upfacfl, upfdrfl, plotBasins = False):
    '''Finds unique pour points between two HUC4s.
    
    Parameters
    ----------
    pourBasins : GeoDataframe
        GeoDataframe of the HUC12 basins that flow into the downstream HUC4. Used to clip the upstream FAC grid to identify pour points.
    upfacfl : str
        Path to the upstream flow accumulation grid.
    upfdrfl : str
        Path to the upstream tauDEM flow direction grid.
    plotBasins : bool (Optional)
        Boolean to make plots of upstream HUC12s and identified pour points. Defaults to False.
        
    Returns
    -------
    finalPoints : list
        List of tuples containing (x,y,w). These pour points have not been incremented downstream and can be used to query accumulated (but not FCPGed) upstream parameter grids for information to cascade down to the next hydrologic region / geospatial tile downstream. 
    '''
    pourPoints = []
    for i in range(len(pourBasins)):
        data = rs.open(upfacfl) # open the FAC grid

        # make a shape out of the HUC boundary
        row = pourBasins.iloc[[i]].copy()
        row['geometry'] = row.buffer(50)

        coords = getFeatures(row)

        out_img, out_transform = mask(data, shapes=coords, crop=True) # get the raster for the HUC

        cx,cy = np.where(out_img[0] == out_img[0].max()) # find the location of max values

        w = out_img[0].max() # get the value to propagate to the downstream grid.

        newx,newy = rs.transform.xy(out_transform,cx,cy) # convert the row, column locations to coordinates given the new affine

        # zip the coordinates to points, when moved downstream, only one of these should land on a no data pixel
        points = [(nx,ny) for nx,ny in zip(newx,newy)]

        # test if a point lands on a noData pixel.
        #print(len(points))
        for point in points:
            x,y = point
            d = queryPoint(x,y,upfdrfl)
            newx,newy = FindDownstreamCellTauDir(d,x,y,out_transform[0]) # move the pour point downstream
            if queryPoint(newx,newy, upfacfl) == data.meta['nodata']:
                pourPoints.append((x,y,w)) # append the pour point to the output list.
    
    if plotBasins:
        ax = pourBasins.plot('Name')
        for px,py,pw in pourPoints:
            ax.scatter(px,py,c='k',s=20)
    
    # get the unique pour points...
    xs,ys,ws = zip(*pourPoints)

    xs = np.array(xs)
    ys = np.array(ys)
    ws = np.array(ws)

    pts = []
    for x,y,w in zip(xs,ys,ws):
        pts.append("%s%s%s"%(x,y,w))

    idx = np.unique(pts,return_index=True)[1]
    
    # use the indicies to make a set of final pour points
    finalPoints = []
    for x,y,w in zip(xs[idx],ys[idx],ws[idx]):
        finalPoints.append((x,y,w))
        
    return finalPoints

def loadRaster(fl, returnMeta = False, band = 1):
    '''Helper function to load raster data and metadata.
    
    Parameters
    ----------
    fl : str
        Path to the raster file to load.
    returnMeta : bool (Optional)
        Return the raster metadata. Defaults to False.
    band : int (Optional)
        Band to read from the raster. Defaults to one.

    Returns
    -------
    dat : np.array
        Numpy array of the data in the selected raster band.
    meta : dict
        Dictionary of raster metadata.
    '''
    try:
        with rs.open(fl) as src:
            dat = src.read(band)
            meta = src.meta.copy()
        
        if returnMeta:
            return dat, meta
        else:
            return dat
    except:
        print("Error - Unable to open %s"%(fl))

def findLastFACFD(facfl, fl = None):
    '''Find the coordinate of the greatest cell in facfl, return the value from fl at that point.
    
    Parameters
    ----------
    facfl : str
        Path to a flow accumulation grid.
    fl : str (optional)
        Path to an accumulated parameter file. Defaults to None. If None, the facfl is queried.
    
    Returns
    -------
    x : float
        Horizontal coordinate of the greatest FAC cell.
    y : float
        Vertical coordinate of the greatest FAC cell.
    d : float
        Value from the parameter grid queried.
    w : float
        Cell size of the grid.


    Notes
    -----
    This can be used to find the flow direction of the FAC cell with the greatest accumulation value or the parameter value of the cell with the greatest accumulation value.
    '''
    
    fac,meta = loadRaster(facfl,returnMeta=True) # load the fac file
    
    if fl is None:
        dat = fac # use the fac raster as the parameter grid to query.
    else:
        dat = loadRaster(fl) # load the data file

    cx,cy = np.where(fac==fac.max()) # find the column, row cooridnates of the max fac.
    
    d = dat[cx,cy][0] # query the parameter grid
    
    src = rs.open(facfl) # open the fac dataset
    x,y = src.xy(cx,cy) # convert the column, row coordinates to map coordinates
    
    w = meta['transform'][0] # get the cell size of the grid
    
    return float(x[0]),float(y[0]),float(d),float(w)

def queryPoint(x,y,grd):
    '''Query grid based on a supplied point.
    
    Parameters
    ----------
    x : float or int
        Horizontal coordinate in grid projection.
    y : float or int
        Vertical coordinate in grid projection.
    grd : str
        Path to raster to query based on the supplied x and y coordinates.
        
    Returns
    -------
    value : float or int
        Value queried from the supplied raster.
    '''
    
    # loop construct is to deal with src.sample returning an array, only the value is needed.
    with rs.open(grd) as src:
        for i in src.sample([(x,y)],1):
            return i[0]

def FindDownstreamCellTauDir(d,x,y,w):
    '''Find downstream cell given the flow direction of a reference cell using TauDEM flow directions.
    
    Parameters
    ----------
    d : int
        Flow direction of the reference cell.
    x : float
        Horizontal coordinate (either projected or unprojected).
    y : float
        Vertical coordinate (either projected or unprojected).
    w : float
        Cell size, in map units.
        
    Returns
    -------
    x : float
        Horizontal coordinate of the downstream cell.
    y : float
        Vertical coordinate of the downstream cell.
    '''
    
    # figure out how to correct the point location
    if d == 1: # east
        dx = w
        dy = 0.
    elif d == 2: # northeast
        dx = w
        dy = w
    elif d == 3: # north
        dx = 0.
        dy = w
    elif d == 4: # northwest
        dx = w*-1.
        dy = w
    elif d == 5: # west
        dx = w*-1.
        dy = 0.
    elif d == 6: # southwest
        dx = w*-1.
        dy = w*-1.
    elif d == 7: # south
        dx = 0.
        dy = w*-1.
    elif d == 8: # southeast
        dx = w
        dy = w*-1.
        
    # update the location
    newX = x+dx
    newY = y+dy
    
    return float(newX),float(newY)

def saveJSON(dictionary, outfl):
    '''Save dictionary to JSON file.
    
    Parameters
    ----------
    dictionary : dict
        Dictionary to be saved.
    outfl : str
        Path for where to generate the JSON
        
    Returns
    -------
    None
    '''
    # Write JSON file
    with io.open(outfl, 'w', encoding='utf8') as outfile:
        str_ = json.dumps(dictionary,
                      indent=4, sort_keys=True,
                      separators=(',', ': '), ensure_ascii=False)
        outfile.write(to_unicode(str_))
    
    return None

def loadJSON(infl):
    '''Load dictionary stored in a JSON file.
    
    Parameters
    ----------
    infl : str
        Path to the JSON to be loaded.
        
    Returns
    -------
    dictionary : dict
        Dictionary that was loaded.
    '''
    # Read JSON file
    with open(infl) as data_file:
        dictionary = json.load(data_file)
    
    return dictionary

def createUpdateDict(x, y, upstreamFACmax, fromHUC, outfl, replaceDict = True, verbose = False):
    '''Create a dictionary for updating downstream FAC and parameter grids using values pulled from the next grid upstream.
    
    Parameters
    ----------
    x : list
        Horizontal coordinate(s) for where the update needs to happen in the downstream grid. 
    y : list
        Vertical coordinate(s) for where the update needs to happen in the downstream grid.
    upstreamFACmax : list
        Value(s) to insert into the downstream FAC grid.
    fromHUC : str
        The upstream HUC that the values are coming from.
    outfl : str (path)
        Path to where to save the json of this dictionary. The convention is to name this by the downstream HUC.
    replaceDict : bool (optional)
        Replace the update dictionary instead of updating with a new value. Defaults to True.
    verbose : bool (optional)
        Print output, defaults to False.
    
    Returns
    -------
    updateDict : dict
        Update dictionary that is also written to outfl.
    '''
    
    # using lists instead of single values in case there are multiple pour points between basins
    
    if type(x) != list:
    	x = list(x)
    if type(y) != list:
    	y = list(y)
    if type(upstreamFACmax) != list:
    	upstreamFACmax = list(upstreamFACmax)

    # convert lists to strings
    xs = [str(xx) for xx in x]
    ys = [str(yy) for yy in y]
    facs = [str(fac) for fac in upstreamFACmax]
    
    subDict = { # make dictionary for the upstream FAC
        'x': xs,
        'y': ys,
        'maxUpstreamFAC':facs,
        'vars':['maxUpstreamFAC'] # list of contained parameters
                }
    
    if os.path.exists(outfl) and replaceDict==False: # if the update dictionary exists, update it.
        if verbose: print('Update dictionary found: %s'%outfl)
        updateDict = loadJSON(outfl)
        if verbose: print('Updating dictionary...')
        updateDict[fromHUC] = subDict
    elif os.path.exists(outfl) and replaceDict==True:
        os.remove(outfl)
        updateDict = {
            fromHUC : subDict
        }
    else:
        updateDict = {
            fromHUC : subDict
        }
        
    saveJSON(updateDict, outfl)
    
    return updateDict

def updateRaster(x,y,val,grd,outgrd, scaleFactor = None):
    '''Insert value into grid at location specified by x,y; writes new raster to output grid.
    
    Parameters
    ----------
    x : list or float
        Horizontal coordinate in map units.
    y : list of float
        Vertical coordinate in map units.
    val : int or float
        Value to insert into raster at grd.
    grd : str
        Path to raster to be updated.
    outgrd : str (path)
        Path to write updated raster to.
    scaleFactor : int (optional)
        Integer value to divide the output raster by when working with very large flow accumulation areas and associated parameter grids, defaults to None.
    
    Returns
    -------
    dat : raster
        Raster dataset written to grdout.
    '''
    
    if type(x) != list:
        x = list(x)
        
    if type(y) != list:
        y = list(y)
        
    if type(val) != list:
        val = list(val)
    
    dat,meta = loadRaster(grd, returnMeta=True)

    if scaleFactor:
        dat /= scaleFactor # scale the input grid
    
    with rs.open(grd) as src: # iterate over the supplied points 
        for xx,yy,vv in zip(x,y,val):
            
            if scaleFactor:
                vv = vv / scaleFactor # correct the value being inserted

            c,r = src.index(float(xx),float(yy)) # get column, row coordinates
            dat[c,r] += int(float(vv)) # update the dataset
            
    meta.update({'dtype': dat.dtype, # update data type
        'compress':'LZW',
        'zlevel':9,
        'interleave':'band',
        'profile':'GeoTIFF',
        'tiled':True,
        'sparse_ok':True,
        'num_threads':'ALL_CPUS',
        'bigtiff':'IF_SAFER',
        'driver' : "GTiff"
    })
            
    with rs.open(outgrd,'w',**meta) as dst: # open dataset for output
        dst.write(dat,1)
    
    return None

def makeFACweight(ingrd,outWeight):
    '''Make FAC weighting grid of ones based on the extents of the input grid. No-data cells are persisted.
    
    Parameters
    ----------
    ingrd : str
        Path to input raster from which to generate the weighting grid from.
    outWeight : str
        Path to the output weighting raster generated.
    
    Returns
    -------
    outWeight : raster
        Raster of the same extent and resolution as the input grid, but filled with ones where data exist. No-data cells are persisted.
    '''
    dat, meta = loadRaster(ingrd, returnMeta=True)
    
    ones = np.ones_like(dat, dtype=np.int32) # make a grid of ones shaped like the original FAC grid. These will be used as a weighting grid that can be corrected.
    
    ones[dat == meta['nodata']] = meta['nodata'] # persist the noData value into the grid
    meta['dtype'] = ones.dtype # update the datatype
    meta.update({
        'compress':'LZW',
        'zlevel':9,
        'interleave':'band',
        'profile':'GeoTIFF',
        'tiled':True,
        'sparse_ok':True,
        'num_threads':'ALL_CPUS',
        'bigtiff':'IF_SAFER',
        'driver' : "GTiff"
    })
    
    with rs.open(outWeight,'w',**meta) as dst:
        dst.write(ones,1)
    
    return None

def adjustFAC(facWeighttemplate, downstreamFACweightFl, updateDictFl, downstreamFDRFl, adjFACFl, cores=1, mpiCall = 'mpiexec', mpiArg = '-n', verbose = False, scaleFactor = None):
    '''Generate an updated flow accumulation grid (FAC) given an update dictionary produced by :py:func:`createUpdateDict`.
    
    Parameters
    ----------
    facWeighttemplate : str
        Path to a FDR or FAC grid used to make the FAC weighting grid.
    downstreamFACweightFl : str
        Path to output the FAC weighting grid.
    updateDictFl : str
        Path to update dictionary used to update the FAC weighting grid.
    downstreamFDRFl : str
        Path to downstream FDR to use when computing the adjusted FAC grid.
    adjFACFl : str
        Path to output the adjusted FAC raster.
    cores : int (Optional)
        Number of cores to use. Defaults to 1.
    mpiCall : str (optional)
        MPI program to use to execute the program, defaults to mpiexec.
    mpiArg : str (optional)
        Argument to pass to mpiCall, defaults to -n.
    verbose : bool (optional)
        Print output, defaults to False.
    scaleFactor : int (optional)
        Value to divide weighting grid by for working with very large flow accumulation values and associated parameter value, defaults to None.
    
    Returns
    -------
    adjFACFl : raster
        Adjusted flow accumulation raster at adjFACFl
    '''
    updateDict = loadJSON(updateDictFl)
    for key in updateDict.keys(): # for each upstream HUC.

        upstreamDict = updateDict[key] # subset out the upstream HUC of interest
        if 'maxUpstreamFAC' in upstreamDict['vars']:
            if not os.path.isfile(downstreamFACweightFl): # If weighting file not present, create one at the supplied path.
                if verbose: print("Generating FAC weighting grid.")
                makeFACweight(facWeighttemplate,downstreamFACweightFl) 
            if os.path.isfile(downstreamFACweightFl): # if the weighting grid is present, update it with the upstream value.
                if verbose: print("Updating FAC weighting grid with value from %s FAC"%(key))
                updateRaster(upstreamDict['x'],
                             upstreamDict['y'],
                             upstreamDict['maxUpstreamFAC'],
                             downstreamFACweightFl,downstreamFACweightFl, scaleFactor = scaleFactor) # update with lists
            
    accumulateParam(downstreamFACweightFl, downstreamFDRFl, adjFACFl, cores = cores) # run a parameter accumulation on the weighting grid.

def updateDict(ud, upHUC, varName, val):
    '''Update dictionary created using :py:func:`createUpdateDict` with a parameter value.
    
    Parameters
    ----------
    ud : str
        Path to the update dictionary to add a parameter to.
    upHUC : str
        Name of the upstream HUC that the parameter corresponds to.
    varName : str
        Name to use for the parameter.
    val : list, int or float
        Value to add to the upstream dictonary.
    
    Returns
    -------
    ud : json
        Update dictionary written back out to ud.
    '''
    
    if type(val) != list:
        val = list(val)
    
    UD = loadJSON(ud)
    
    upstream = UD[upHUC]
    variables = upstream['vars']
    variables.append(varName)
    variables = list(np.unique(variables))
    upstream['vars'] = variables
    
    upstream[varName] = val
    
    UD[upHUC] = upstream # update dictionary with upstream sub-dictionary
    saveJSON(UD, ud) # write out file

def adjustParam(updatedParam, downstreamParamFL, updateDictFl, adjParamFl, verbose = False, scaleFactor = None):
    '''Generate an updated parameter grid given an update dictionary from :py:func:`createUpdateDict`.
    
    Parameters
    ----------
    updatedParam : str
        Name of the parameter to update.
    downstreamParamFL : str
        Path to downstream parameter grid to update.
    updateDictFl : str
        Path to update dictionary to use.
    adjParamFl : str
        Path to output adjusted parameter file.
    verbose : bool (optional)
        Print output, defaults to False.
    
    Returns
    -------
    adjParamFl : raster
        Adjusted parameter raster that can be accumulated prior to FCPG creation.
    '''
    updateDict = loadJSON(updateDictFl)
    for key in updateDict.keys(): # for each upstream HUC.

        upstreamDict = updateDict[key] # subset out the upstream HUC of interest
        if updatedParam in upstreamDict['vars']: 
            if os.path.isfile(downstreamParamFL): # if the weighting grid is present, update it with the upstream value.
                if verbose: print("Updating parameter grid with value from %s FAC"%(key))
                updateRaster(upstreamDict['x'],
                             upstreamDict['y'],
                             upstreamDict[updatedParam],
                             downstreamParamFL,adjParamFl, scaleFactor = scaleFactor) # update with lists

def d8todinfinity(inRast, outRast, updateDict = {
                'dtype':'float32',
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-1,
                'bigtiff':'IF_SAFER'}, verbose = False):
    """Convert TauDEM D-8 flow directions to D-Infinity flow directions.

    Parameters
    ----------
    inRast : str
        Path to a TauDEM D-8 flow direction raster.
    outRast : str
        Path to output the TauDEM D-Infinity flow direction raster.
    updateDict : dict (optional)
        Dictionary of Rasterio parameters used to write out the GeoTiff.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    outRast : str
        Path to output the TauDEM D-Infinity flow direction raster.
    """

    if verbose: print('Reclassifying Flow Directions...')

    # load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

    tauDir = dat.copy()
    tauDir = tauDir.astype('float32')#Store as 32bit float
    tauDir[dat == inNoData] = np.nan #Set no data to nan

    tauDir = (tauDir - 1) * np.pi/4

    tauDir[tauDir == np.nan] = -1 # no data
    
    # edit the metadata
    profile.update(updateDict)

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(tauDir,1)
        if verbose: print("TauDEM drainage direction written to: {0}".format(outRast))

def changeNoData(inRast, newNoData, updateDict = {
                'compress':'LZW',
                'zlevel':9,
                'interleave':'band',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'bigtiff':'IF_SAFER'}, verbose = False):
    """Update raster no data value to a new value.

    Parameters
    ----------
    inRast : str
        Path to input raster file.
    newNoData : str
        New no data value for the raster.
    updateDict : dict (optional)
        Dictionary of Rasterio parameters used to create the updated raster.
    verbose : bool (optional)
        Print output, defaults to False.

    Returns
    -------
    None
    """
    
    if verbose: print('Opening raster...')

    #load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

    if verbose: print('Changing no data values...')
    dat[dat == inNoData] = newNoData #Change no data value

    updateDict['nodata'] = newNoData # add new noData value to the update dictionary.

    # edit the metadata
    profile.update(updateDict)

    with rs.open(inRast,'w',**profile) as dst:
        dst.write(dat,1)
        if verbose: print("Raster written to: {0}".format(inRast))

# def makeStreams(fac, strPath, thresh = 900, updateDict = {
#                 'nodata':99,
#                 'compress':'LZW',
#                 'zlevel':9,
#                 'interleave':'band',
#                 'profile':'GeoTIFF',
#                 'tiled':True,
#                 'sparse_ok':True,
#                 'num_threads':'ALL_CPUS',
#                 'bigtiff':'IF_SAFER'}, verbose = False):
#     """Create stream grid from a flow accumulation grid based on a threshold value.

#     Parameters
#     ----------
#     fac : str
#         Path to the flow accumulation grid that will be used to create the stream grid.
#     strPath : str
#         Path to output the stream grid where stream cells will be 1 and other cells will be the no-data value from the source fac grid.
#     thresh : int (optional)
#         Flow accumulation threshold above which streams are created, defaults to 900 cells.
#     updateDict : dict (optional)
#         Rasterio raster creation parameters.
#     verbose : bool (optional)
#         Print output, defaults to False.

#     Returns
#     -------
#     None

#     """

#     assert os.path.isfile(fac), "fac not found."
#     if verbose: print('Loading fac')
#     with rs.open(fac) as ds:
#         dat = ds.read(1)
#         profile = ds.profile.copy()

#     strRast = np.zeros_like(dat, dtype = np.int8)
#     strRast[:] = updateDict['nodata'] # fill with no-data values
#     strRast[dat>=thresh] = 1 # make cells at or above the threshold 1

#     profile.update(updateDict) # update the raster profile
#     profile['dtype'] = str(strRast.dtype)

#     if verbose: print(profile)

#     with rs.open(strPath,'w',**profile) as dst:
#         dst.write(strRast,1) # write out the geotiff