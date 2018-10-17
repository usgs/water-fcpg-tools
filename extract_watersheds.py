#!/usr/bin/env python2
# script to extract watershed areas from gauges snapped to NHDplusV2.1
# Theodore Barnhart | August 22, 2018 | tbarnhart@usgs.gov
from __future__ import print_function #python 2/3
from grass.pygrass.modules import Module
import sys
import subprocess
import os
import pandas as pd
from pyproj import Proj, transform
import numpy as np

reg = sys.argv[1] # extract coommand line argument 1, region to process
#reg = '16'

workspace = '/home/tbarnhart/projects/DEM_processing/data'
drainDirPath = os.path.join(workspace,'NHDplusV21_facfdr','region_%s_fdr_grass.tiff'%(reg))

fl = os.path.join(workspace,'CATCHMENT_gauges/CATCHMENT_reg_%s_snapped_ID.csv'%reg)
gauges = pd.read_csv(fl)

# now for the GRASS code

# define functions to use
r_external = Module('r.external')
r_water_outlet = Module('r.water.outlet')
r_to_vect = Module('r.to.vect')
v_out_ogr = Module('v.out.ogr')
g_region = Module('g.region') # command to set processing region extent and resolution
v_db_addcol = Module('v.db.addcolumn')
v_to_db = Module('v.to.db')

r_external(input=drainDirPath,output='dir', o = True, overwrite = True) # bring in the drainage direction raster
g_region(raster = 'dir', res = 30) # set region resolution and extent
#r_external() # link the accumulation raster

for ID,x,y in zip(gauges.Gage_no,gauges.x,gauges.y):
    print('Starting Gauge No. %s in Region %s.'%(ID,reg))
    outfl = os.path.join(workspace,'gauges','region_%s_gageNo_%s_watershed_NHDplusV2_1.shp'%(reg,ID)) # format output string

    if os.path.isfile(outfl):
        print('Gauge No. %s in Region %s already complete.'%(ID,reg))
        continue

    else:

        r_water_outlet(input = 'dir', output = 'watershed', coordinates =(x,y), overwrite=True, quiet = True) # delineate watershed
        r_to_vect(input = 'watershed', output = 'boundary', type = 'area', overwrite=True, quiet = True) # convert raster to vector

        # compute area of watershed
        v_db_addcol(map='boundary', columns='area_sqkm double precision', quiet = True)
        v_to_db(map='boundary', option='area', columns='area_sqkm', units='kilometers', quiet = True)

        v_out_ogr(e = True, input = 'boundary', type = 'area', output = outfl, overwrite=True, format = 'ESRI_Shapefile', quiet = True) # export the watershed boundary to a temporary file

        print('Gauge No. %s in Region %s complete.'%(ID,reg))
