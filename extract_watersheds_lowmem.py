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

output = True

reg = sys.argv[1] # extract coommand line argument 1, region to process
#reg = '16'

workspace = '/home/tbarnhart/projects/DEM_processing/data'
drainDirPath = os.path.join('./data','NHDplusV21_facfdr','region_%s_fdr_grass.tiff'%(reg))
elevPath = os.path.join('./data','NHDplusV21','region_%s.vrt'%(reg)) # path to elevation data

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
r_buffer = Module('r.buffer')
r_watershed = Module('r.watershed')

r_external(input=drainDirPath,output='dir', o = True, overwrite = True) # bring in the drainage direction raster
r_external(input=elevPath,output = 'elev', o = True, overwrite = True) # bring in the NHDplus V2.1 elevation raster 

# set some coarsening parameters
coarseRes = 300
Res = 30
buffDist = 900

g_region(raster = 'elev') # set region extent
g_region(res = coarseRes, a=True) # set region resolution
if output: g_region(p=True) # print region for debug

r_watershed(elevation = 'elev', drainage = 'dir_coarse', m = True, memory = 99000, overwrite = True, quiet = True) # compute re-sampled drainage direction...
if output: print('drainage direction computed')

for ID,x,y in zip(gauges.Gage_no,gauges.x,gauges.y):
    #print('Starting Gauge No. %s in Region %s.'%(ID,reg))
    outfl = os.path.join(workspace,'gauges','region_%s_gageNo_%s_watershed_NHDplusV2_1.shp'%(reg,ID)) # format output string

    if os.path.isfile(outfl):
        print('Gauge No. %s in Region %s already complete.'%(ID,reg))
        continue

    else:
        print('Starting Gauge No. %s in Region %s.'%(ID,reg))
        
        # reset region to full extent, reduced resolution
        
        cmd = 'sh extract.sh %s %s %s %s %s %s'%(coarseRes,Res,buffDist,outfl,x,y)

        subprocess.call(cmd, shell=True)

        print('Gauge No. %s in Region %s complete.'%(ID,reg))
