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

def getNHDPlusRaster(HUC, path):
    """
    Inputs:
        HUC - HUC code of region to download
        path - path to store raster files
    """


def tauDrainDir(inRast, outRast):
    """
    Inputs:
        inRast - Flow direction raster from NHDPlus

    Outputs:
        outRast - Flow direction raster for tauDEM
    """

    print('Reclassifying Flow Directions')

    # load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        meta = ds.meta.copy() # save the metadata for output later

    # edit the metadata
    meta.update({'driver':'GTiff'})
    meta.update({'nodata':-1})

    #print(meta)

    tauDir = dat.copy()
    # remap NHDplus flow direction to TauDEM flow Direction
    # east is ok
    tauDir[dat == 1] = 1 # east
    tauDir[dat == 2] = 8 # stauDirheast
    tauDir[dat == 4] =  7 # stauDirh
    tauDir[dat == 8] = 6 # stauDirhwest
    tauDir[dat == 16] = 5 # west
    tauDir[dat == 32] = 4 # northwest
    tauDir[dat == 64] = 3 # north
    tauDir[dat == 128] = 2 # northeast
    tauDir[dat == -2147483648] = -1 # no data
    
    with rs.open(outRast,'w',**meta) as dst:
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


def accumulateParam(paramRast, fdr, outRast, cores = 1):
    """
    Inputs:
        paramRast - Raster of parameter values to acumulate
        fdr - flow direction raster in tauDEM format
        cores - number of cores to use parameter accumulation

    Outputs:
        outRast - raster of accumulated parameter values
    """

    # first accumulate the parameter
    try:
        print('Accumulating Data')
        tauParams = {
        'fdr':fdr,
        'cores':cores
        }
        
        tauParams['outFl'] = outRast
        tauParams['weight'] = paramRast
        
        cmd = 'mpiexec -n {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams)
        print(cmd)
        result = subprocess.run(cmd, shell = True)
        result.stdout
        
        print('Parameter accumulation written to: %s'%outRast)
    except:
        print('Error Accumulating Data')
        traceback.print_exc()

    
def make_cpg(accumParam, fac, outRast):
    '''
    Inputs:
        
        daccumParam - path to the accumulated parameter data raster
        
        fac - flow accumulation grid path
        outRast - output file
        

    Outputs:
        Parameter and NoData CPGS as bands 1 and 2 of a file in the output directory.
    '''
    outNoData = -9999
    

    with rs.open(accumParam) as ds: # load accumulated data and no data rasters
        data = ds.read(1)
        profile = ds.profile

    #with rs.open(noDataPath) as ds:
     #   noData = ds.read(1)

    with rs.open(fac) as ds: # flow accumulation raster
        accum = ds.read(1)
        accumNoData = ds.nodata # pull the accumulated area no data value
        print("No Data Value:%s"%str(ds.nodata))
        
    accum2 = accum.astype(np.float32)
    accum2[accum == accumNoData] = np.NaN # fill this with no data values where appropriate
    
    
    # zero negative accumulations Should we throw some sort of warning if there is a negative accumulation?
    if np.min(accum2) < 0:
        print("Warning: Negative accumulation value")
        print("Minimum value:%s"%str(np.min(accum2)))
    """
    accum[accum < 0] = 0 
    noData[noData < 0] = 0
    data[data < 0] = 0

    corrAccum = (accum - noData) # compute corrected accumulation
    addition = np.min(corrAccum) # find the minumum value, since the denominator cannot be zero

    if addition > 0: # if the minumum value is positive, make addition zero
        addition = 1
    else: # otherwise, make the addition the absolute value of the minimim to bring the corrAccum min to + 1
        addition = np.abs(addition) + 1
    
    dataCPG = data / (corrAccum + addition) # make data CPG, correct for negative values if any
    
    noDataCPG = noData / (corrAccum + addition) # make noData CPG
    """
    
    dataCPG = data / (accum2 + 1)# make data CPG
    
    #noDataCPG = noData / (corrAccum + addition) # make noData CPG
    
    # fill edges with no data, not sure this is the correct thing to do.
    dataCPG[np.isnan(accum2)] = outNoData
    #noDataCPG[np.isnan(accum2)] = outNoData

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
        #dst.write(noDataCPG,2)

def resampleParam(inParam, fdr, outParam, resampleMethod):
    '''
    Inputs:
        
        inParam - input parameter data raster
        fdr - flow direction raster
        
        outParam - output file for resampled parameter raster
        resampleMethod - resampling method 

    Outputs:
        Parameter and NoData CPGS as bands 1 and 2 of a file in the output directory.
    '''
    from rasterio.warp import reproject, Resampling

    inParamRaster = rs.open(inParam)
    src_crs = inParamRaster.crs
    src_transform = inParamRaster.transform
    src_nodata = inParamRaster.nodata

    with rs.open(inParam) as ds: # load accumulated data and no data rasters
        inParamRaster = ds.read(1)
        profile = ds.profile

    fdrRaster = rs.open(fdr)# load flow direction raster
  
    
    fdrcrs = fdrRaster.crs #Get flow direction coordinate system
    xsize, ysize = fdrRaster.res
    fdrtransform = fdrRaster.transform
    fdrnodata = fdrRaster.nodata

    profile.update({
                'profile':'GeoTIFF',
                'crs':fdrcrs,
                'transform':fdrtransform,
                'num_threads':'ALL_CPUS',
                'nodata': fdrnodata,
                })
    
    print("x cell:%s"%xsize)
    print("y cell:%s"%ysize)

    with rs.open(outParam, 'w', **profile) as dst:
        reproject(inParamRaster, rs.band(dst, 1), src_transform=src_transform, dst_transform=fdrtransform, src_crs=src_crs, dst_crs = fdrcrs, src_nodata=src_nodata, dst_nodata=fdrnodata, resampling = Resampling.bilinear)



def downloadNHDPlusRaster(HUC4, filePath):
    compressedFile = os.join(filePath, HUC4, "_RASTER.7z")
    urllib.urlretrieve ("https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHDPlus/HU4/HighResolution/GDB/NHDPLUS_H_%s_HU4_RASTER.7z"%str(HUC4), compressedFile)

    os.system( '7z x compressedFile -o filePath')