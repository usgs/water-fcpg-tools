import rasterio as rs
import numpy as np

# Script to destroy the netCDF file Roy got from gridMET

netCDFpath = "../data/cov/gridMET_PRmm.tif"

with rs.open(netCDFpath) as ds: # load parameter raster
        numBands = ds.count
        data = ds.read()
        profile = ds.profile
        paramNoData = ds.nodata
        tags = ds.tags()

i = 0 

for band in data:

        


        i = i + 1

