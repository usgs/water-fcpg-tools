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

    print('Opening raster...')

    # load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later

     print('Replacing NaNs...')

    #fix = np.nan_to_num(dat,  nan=-9999, posinf=-9999, neginf=-9999)
    fix = np.nan_to_num(dat)

    fix = fix.astype('float32')

    # edit the metadata
    profile.update({
                'dtype':'float32',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-9999,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(fix,1)
        print("Raster written to: {0}".format(outRast))



nan2nodata("../data/cov/landsatNDVI/NDVI_May_Oct_Composite_2012-0000000000-0000000000.tif", "../data/cov/landsatNDVI/NDVI_May_Oct_Composite_2012-0000000000-0000000000fix.tif")