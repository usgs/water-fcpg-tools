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




def changeNoData(inRast, newNoData):
    """
    Inputs:
        inRast - Input raster file path
        newNoData - new no data value for the raster

    """
    
    print('Opening raster...')

    #load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

    print('Changing no data values...')
    dat[dat == inNoData] = newNoData #Change no data value

    # edit the metadata
    profile.update({
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':newNoData,
                'bigtiff':'IF_SAFER'})

    with rs.open(inRast,'w',**profile) as dst:
        dst.write(fix,1)
        print("Raster written to: {0}".format(outRast))





inDir = "../data/cov/landsat_NDVI-May-Oct2"

covList = [] #Initialize list of covariates

if os.path.isdir(inDir):
    #Get all covariate files in directory
    for path, subdirs, files in os.walk(inDir):
        for name in files:
            #Check if file is .tif, and if so add it to covariate list
            if os.path.splitext(name)[1] == ".tif":
                    covList.append(os.path.join(path, name))
elif os.path.isfile(inDir):
    #Supplied path is a single covariate file
    covList.append(inDir)
else:
    print("Invalid covariate directory")

print("The following covariate files were located in the specified directory:")
print(covList)

for cov in covList:

    changeNoData(cov, -3.4028234663852886e+38)
