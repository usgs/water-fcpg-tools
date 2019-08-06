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




def nan2nodata(inRast, outRast):
    """
    Inputs:
        inRast - Input raster file path

    Outputs:
        outRast - Output raster file path
    """
    

    outNoData = -9999  #Must be set to zero for numpy < 1.17
    print('Opening raster...')

    #load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

    print('Replacing NaNs...')

    fix = np.nan_to_num(dat,  nan=outNoData, posinf=outNoData, neginf=outNoData)
    #fix = np.nan_to_num(dat)

    fix = fix.astype('float32')

    # edit the metadata
    profile.update({
                'dtype':'float32',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(fix,1)
        print("Raster written to: {0}".format(outRast))





inDir = "../data/cov/landsatNDVI"
outDir = "../data/cov/landsat_NDVI-May-Oct"

covList = [] #Initialize list of covariates

if os.path.isdir(inDir):
    #Get all covariate files in directory
    for path, subdirs, files in os.walk(inDir):
        for name in files:
            #Check if file is .tif, and if so add it to covariate list
            if os.path.splitext(name)[1] == ".vrt":
                    covList.append(os.path.join(path, name))
elif os.path.isfile(inDir):
    #Supplied path is a single covariate file
    covList.append(inDir)
else:
    print("Invalid covariate directory")

print("The following covariate files were located in the specified directory:")
print(covList)

for cov in covList:

    covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate

    outfile = os.path.join(outDir, "{0}fix.tif".format(cov)) # Create path to output file
        
    print("Creating: " + outfile)

    nan2nodata(cov, outfile)
