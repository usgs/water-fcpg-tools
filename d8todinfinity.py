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
import urllib.request
import datetime
from multiprocessing import Pool as processPool
from osgeo import osr




def d8todinfinity(inRast, outRast):
    """
    Inputs:
        inRast - tauDEM d8 flow direction raster

    Outputs:
        outRast - tauDEM dinfinity flow direction raster
    """

    print('Reclassifying Flow Directions...')

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
    profile.update({
                'dtype':'float32',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-1,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(tauDir,1)
        print("TauDEM drainage direction written to: {0}".format(outRast))



inFile = "../data/tauDEM/taufdr1002.tif"
outFile = "../data/tauDEM/taudINFang1002.tif"

d8todinfinity(inFile, outFile)