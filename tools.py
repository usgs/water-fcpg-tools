import rasterio as rs
import numpy as np
import sys
import os
import pandas as pd
import gdal
import subprocess
import glob
import shutil
import traceback
import urllib
from multiprocessing import Pool as processPool

def tauDrainDir(inRast, outRast):
    """
    Inputs:
        inRast - Flow direction raster from NHDPlus

    Outputs:
        outRast - Flow direction raster for tauDEM
    """

    print('Reclassifying Flow Directions...')
    import time

    # load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later



    tauDir = dat.copy()
    # remap NHDplus flow direction to TauDEM flow Direction
    # east is ok
    
    #tauDir[dat == 1] = 1 # east
    tauDir[dat == 2] = 8 # stauDirheast
    tauDir[dat == 4] =  7 # stauDirh
    tauDir[dat == 8] = 6 # stauDirhwest
    tauDir[dat == 16] = 5 # west
    tauDir[dat == 32] = 4 # northwest
    tauDir[dat == 64] = 3 # north
    tauDir[dat == 128] = 2 # northeast
    tauDir[dat == inNoData] = -1 # no data
    #tauDir = tauDir.astype('int8')#8 bit integer is sufficient for flow directions

    # edit the metadata
    profile.update({
                #'dtype':'int8',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-1,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(tauDir,1)

    print('TauDEM drainage direction written to: %s'%outRast)

#print(np.shape(tauDir))

def grassDrainDir(inRast, outRast):
    """
    Inputs:
        inRast - Flow direction raster from NHDPlus

    Outputs:
        outRast - Flow direction raster for GRASS
    """

    grassDir = dat.copy()
    # remap NHDplus flow direction to GRASS flow direction
    grassDir[dat == 128] = 1 # northeast
    grassDir[dat == 64] = 2 # north
    grassDir[dat == 32] = 3 # northwest
    grassDir[dat == 16] = 4 # west
    grassDir[dat == 8] = 5 # southwest
    grassDir[dat == 4] = 6 # south
    grassDir[dat == 2] = 7 # southeast
    grassDir[dat == 1] = 8 # east

    with rs.open(outRast,'w',**meta) as dst:
        dst.write(grassDir,1)

    print('GRASS drainage direction written to: %s'%outRast)


def accumulateParam(paramRast, fdr, accumRast, outNoDataRast = None, cores = 1):
    """
    Inputs:
        paramRast - Raster of parameter values to acumulate, this file is modified by the function
        fdr - flow direction raster in tauDEM format
        outNoDataRast - raster of accumulated no data values
        cores - number of cores to use parameter accumulation

    Outputs:
        mskRast - parameter raster masked to flow direction raster
        accumRast - raster of accumulated parameter values
    """

    with rs.open(paramRast) as ds: # load parameter raster
        data = ds.read(1)
        profile = ds.profile
        paramNoData = ds.nodata

    with rs.open(fdr) as ds: # load flow direction raster
        direction = ds.read(1)
        directionNoData = ds.nodata # pull the accumulated area no data value


    #Deal with no data values
    basinNoDataCount = len(data[(data == paramNoData) & (direction != directionNoData)]) # Count number of cells with flow direction but no parameter value
    
    if basinNoDataCount > 0:
        print('Warning: No data parameter values exist in basin')

        #If a no data file path is given, accumulate no data values
        if outNoDataRast != None:
            noDataArray = data.copy()
            noDataArray[(data == paramNoData) & (direction != directionNoData)] = 1 #Set no data values in basin to 1
            noDataArray[(data == paramNoData) & (direction == directionNoData)] = -1 #Set no data values outside of basin to -1
            noDataArray[(data != paramNoData)] = 0 #Set values with data to 0
            noDataArray = noDataArray.astype(np.int8)

            # Update profile for no data raster
            profile.update({
                    'dtype':'int8',
                    'compress':'LZW',
                    'profile':'GeoTIFF',
                    'tiled':True,
                    'sparse_ok':True,
                    'num_threads':'ALL_CPUS',
                    'nodata':-1,
                    'bigtiff':'IF_SAFER'})
            
            # Save no data raster
            with rs.open(outNoDataRast, 'w', **profile) as dst:
                dst.write(noDataArray,1)
                print('Parameter No Data raster written to: %s'%outNoDataRast)
    
            # Use tauDEM to accumulate no data values
            try:
                print('Accumulating NO Data Values')
                tauParams = {
                'fdr':fdr,
                'cores':cores, 
                'outFl':outNoDataRast,
                }
                
                cmd = 'mpiexec -n {cores} aread8 -p {fdr} -ad8 {outFl} -nc'.format(**tauParams) # Create string of tauDEM shell command
                print(cmd)
                result = subprocess.run(cmd, shell = True) # Run shell command
                result.stdout
                print('Parameter no data accumulation written to: %s'%outNoDataRast)
                
            except:
                print('Error Accumulating Data')
                traceback.print_exc()


    #Use tauDEM to accumulate the parameter
    try:
        print('Accumulating Data')
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'outFl':accumRast, 
        'weight':paramRast
        }
        
        cmd = 'mpiexec -n {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout
        print('Parameter accumulation written to: %s'%accumRast)

    except:
        print('Error Accumulating Data')
        traceback.print_exc()

    
def make_cpg(accumParam, fac, outRast, noDataRast = None, minAccum = None):
    '''
    Inputs:
        
        accumParam - path to the accumulated parameter data raster
        
        fac - flow accumulation grid path
        outRast - output file
        minAccum - Value of flow accumulation below which the CPG values will be set to no data
        

    Outputs:
        outRast - Parameter CPG 
    '''
    outNoData = -9999
    

    with rs.open(accumParam) as ds: # load accumulated data and no data rasters
        data = ds.read(1)
        profile = ds.profile

    with rs.open(fac) as ds: # flow accumulation raster
        accum = ds.read(1)
        accumNoData = ds.nodata # pull the accumulated area no data value

    accum2 = accum.astype(np.float32)
    accum2[accum == accumNoData] = np.NaN # fill this with no data values where appropriate

    if noDataRast != None:
        with rs.open(noDataRast) as ds: # accumulated no data raster
            accumNoData = ds.read(1)
            noDataNoData = ds.nodata # pull the accumulated no data no data value
        
        accumNoData2 = accumNoData.astype(np.float32)
        accumNoData2[accumNoData == noDataNoData] = np.NaN

        corrAccum = accum2 - accumNoData2 # Compute corrected accumulation
    
    else:
        corrAccum = accum2 # No correction required
        


    
    
    # Throw warning if there is a negative accumulation
    if np.min(corrAccum) < 0:
        print("Warning: Negative accumulation value")
        print("Minimum value:%s"%str(np.min(acorrAccum)))
 


    dataCPG = data / (corrAccum + 1) # make data CPG
    
    
    dataCPG[np.isnan(dataCPG)] = outNoData # Replace numpy NaNs with no data value

    # Replace values in cells with small flow accumulation with no data
    if minAccum != None:
        dataCPG[corrAccum < minAccum] = outNoData #Set values smaller than threshold to no data

    # Updata raster profile
    profile.update({'dtype':dataCPG.dtype,
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'count':2,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(dataCPG,1)

def resampleParam(inParam, fdr, outParam, resampleMethod="bilinear", cores=1):
    '''
    Inputs:
        
        inParam - input parameter data raster
        fdr - flow direction raster
        
        outParam - output file for resampled parameter raster
        resampleMethod (str)- resampling method, either bilinear or nearest neighbor

    Outputs:
        Resampled, reprojected, and clipped parameter raster
    '''

    fdrRaster = rs.open(fdr)# load flow direction raster in Rasterio
  
    fdrcrs = fdrRaster.crs #Get flow direction coordinate system
    xsize, ysize = fdrRaster.res #Get flow direction cell size
    fdrtransform = fdrRaster.transform #Get flow direction affine transform
    fdrnodata = fdrRaster.nodata #Get flow direction no data value

    paramRaster = rs.open(inParam)# load parameter raster in Rasterio
    paramNoData = paramRaster.nodata
    paramType = paramRaster.dtypes[0] #Get datatype of first band

    # Choose an appropriate gdal data type for the parameter
    if paramType == 'int8' or paramType == 'int16':
        outType = 'Int16' # Convert 8 bit integers to 16 bit in gdal
    elif paramType == 'int32':
        outType = 'Int32'
    elif paramType == 'int64':
        outType = 'Int64'
    elif paramType == 'float32':
        outType = 'Float32'
    else:
        print("Warning: Unsupported data type %s"%paramType)
        print("Defaulting to Float64")
        outType = 'Float64' # Try a 64 bit complex floating point if all else fails

    #Get bounding coordinates of the flow direction raster
    fdrXmin = fdrRaster.transform[2]
    fdrXmax = fdrXmin + xsize*fdrRaster.width
    fdrYmax = fdrRaster.transform[5]
    fdrYmin = fdrYmax - ysize*fdrRaster.height

    

    # Resample, reproject, and clip the parameter raster with GDAL
    try:
        print('Resampling and Reprojecting Parameter Raster...')
        warpParams = {
        'inParam': inParam,
        'outParam': outParam,
        'fdr':fdr,
        'cores':cores, 
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
        
        cmd = 'gdalwarp -overwrite -tr {xsize} {ysize} -t_srs {fdrcrs} -te {fdrXmin} {fdrYmin} {fdrXmax} {fdrYmax} -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -r {resampleMethod} -dstnodata {nodata} -ot {datatype} {inParam} {outParam}'.format(**warpParams)
        print(cmd)
        result = subprocess.run(cmd, shell = True)
        result.stdout
        
        print('Parameter reprojected to: %s'%outParam)
    except:
        print('Error Reprojecting Parameter Raster')
        traceback.print_exc()
    


def resampleParams(inParams, fdr, outWorkspace, resampleMethod="bilinear", cores=1, appStr="rprj"):
    '''
    Inputs:
        
        inParam - list of input parameter rasters
        fdr - flow direction raster
        
        outWorkspace - output directory for resampled rasters
        resampleMethod (str)- resampling method, either bilinear or nearest neighbor
        cores = number of cores to use
        appStr = String of text to append to filename

    Outputs:
        Resampled, reprojected, and clipped parameter rasters

    Returns:
        List of fielpaths to resampled rasters
    '''

    fileList = [] #Initialize list of output files

    for param in inParams:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention

        
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        resampleParam(param, fdr, outPath, resampleMethod, cores) #Run the resample function for the parameter raster

    return fileList

def accumulateParams(paramRasts, fdr, outWorkspace, cores = 1, appStr="accum"):
    '''
    Inputs:
        
        paramRasts - list of input parameter rasters to accumulate
        fdr - flow direction raster
        
        outWorkspace - output directory for accumulation rasters
        cores = number of cores to use
        appStr = string of text to append to filename

    Outputs:
        raster of accumulated parameter values

    Returns:
        list of fielpaths to accumulated parameter rasters
    '''

    fileList = [] #Initialize list of output files
    
    for param in paramRasts:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        accumulateParam(param, fdr, outPath, cores) #Run the flow accumulation function for the parameter raster

    """
    processCores = min(4, cores) # Set number of cores used by each process to 4 or the number of available cores
    numProcess = floor(cores / processCores) # Compute the number of processes to create

    from functools import partial
    pool = processPool(processes=numProcess)

    # Use pool.map() to call tauDEM accumulation in parallel
    fileList = pool.map(partial(accumulateParam, fdr, outPath, processCores), paramRasts)

    #close the pool and wait for the work to finish
    pool.close()
    pool.join(
    """



    return fileList

def make_cpgs(accumParams, fac, outWorkspace, minAccum=None, appStr="CPG"):
    '''
    Inputs:
        
        accumParams - list of accumulated parameter rasters to create CPGs from
        fac - flow accumulation raster
        
        outWorkspace - output directory for CPGs
        appStr = string of text to append to filename

    Outputs:
        CPG

    Returns:
        list of fielpaths to parameter CPGs
    '''

    fileList = [] #Initialize list of output files

    for param in accumParams:

        baseName = os.path.splitext(os.path.basename(param))[0] #Get name of input file without extention
        ext = ".tif" #File extension

        outPath = os.path.join(outWorkspace, baseName + appStr + ext)
        fileList.append(outPath)

        make_cpg(param, fac, outPath, minAccum=minAccum) #Run the CPG function for the accumulated parameter raster

    return fileList

def cat2bin(inCat, outWorkspace):
    '''
    Inputs:
        
        inCat - input catagorical parameter raster
        outWorkspace - workspace to save binary raster outputs
        
    Outputs:
        Binary rasters for each parameter category

    Returns:
        List of filepaths to output files
    '''
    print("Creating binaries for %s"%inCat)
    

    baseName = os.path.splitext(os.path.basename(inCat))[0] #Get name of input file without extention
    ext = ".tif" #File extension

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
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-1,#Use -1 as no data value
                'bigtiff':'IF_SAFER'})

    #Create binary rasters for each category
    """
    for n in cats:
        catData = dat.copy()
        catData[(dat != n) & (dat != nodata)] = 0
        catData[dat == n] = 1
        catData[dat == nodata] = -1 #Use -1 as no data value
        catData = catData.astype('int8')#8 bit integer is sufficient for zeros and ones

        catRasterName = baseName + str(n) + ext
        catRaster = os.path.join(outWorkspace, catRasterName)
        fileList.append(catRaster)

        print("Saving %s"%catRaster)
        with rs.open(catRaster,'w',**profile) as dst:
            dst.write(catData,1)
    """
    from functools import partial
    pool = processPool()

    # Use pool.map() to create binaries in parallel
    fileList = pool.map(partial(binarizeCat, data=dat, nodata=nodata, outWorkspace=outWorkspace, baseName=baseName, ext=ext, profile=profile), cats)

    #close the pool and wait for the work to finish
    pool.close()
    pool.join()
    
    
    return fileList



def binarizeCat(val, data, nodata, outWorkspace, baseName, ext, profile):

    '''
    Inputs:
        
        data - numpy arrary of raster data to convert to binary
        val - raster value to extract binary for
        nodata - raster no data value
        outWorkspace - workspace to save binary raster outputs
        baseName - base name for the raster output
        ext - file extension for raster output
        
    Outputs:
        Binary raster the specified parameter value

    Returns:
        Filepath to output files
    '''

    catData = data.copy()
    catData[(data != val) & (data != nodata)] = 0
    catData[data == val] = 1
    catData[data == nodata] = -1 #Use -1 as no data value
    catData = catData.astype('int8')#8 bit integer is sufficient for zeros and ones

    catRasterName = baseName + str(val) + ext
    catRaster = os.path.join(outWorkspace, catRasterName)

    print("Saving %s"%catRaster)
    with rs.open(catRaster,'w',**profile) as dst:
        dst.write(catData,1)
    

    return catRaster # Return the path to the raster created
    






def downloadNHDPlusRaster(HUC4, filePath):
    compressedFile = os.join(filePath, HUC4, "_RASTER.7z")
    urllib.urlretrieve ("https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHDPlus/HU4/HighResolution/GDB/NHDPLUS_H_%s_HU4_RASTER.7z"%str(HUC4), compressedFile)

    os.system( '7z x compressedFile -o filePath')