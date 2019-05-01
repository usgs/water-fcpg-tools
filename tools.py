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

    
