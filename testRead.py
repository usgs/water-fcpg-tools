
import numpy as np
import datetime as dt
import rasterio as rs
import os
import sys
#import re
np.set_printoptions(threshold=sys.maxsize)


inRast = '../CPGs/nc/testInput/gridMET_minTempK_1979_01_00_HUC1002_CPG.tif'
outRast = '../CPGs/nc/testRead.tif'


with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later


print(dat[5000:6000, 5000:6000])

with rs.open(outRast,'w',**profile) as dst:
        dst.write(dat,1)
        

