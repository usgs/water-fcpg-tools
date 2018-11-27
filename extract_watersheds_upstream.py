#!/usr/bin/env python2
# script to extract watershed areas from gauges snapped to NHDplusV2.1
# Theodore Barnhart | August 22, 2018 | tbarnhart@usgs.gov
from __future__ import print_function #python 2/3
from grass.pygrass.modules import Module
import grass.script.array as garray
import sys
import os
import pandas as pd
import numpy as np

reg = sys.argv[1] # extract coommand line argument 1, region to process
#reg = '16'

workspace = '/home/tbarnhart/projects/DEM_processing/data'
drainDirPath = os.path.join(workspace,'NHDplusV21_facfdr','region_%s_fdr_grass.tiff'%(reg))

fl = os.path.join(workspace,'CATCHMENT_gauges/CATCHMENT_region_%s_snapped_fixed.csv'%reg) # load the dataframe with upstream gageNos / Cats
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
v_in_ascii = Module('v.in.ascii')
r_in_gdal = Module('r.in.gdal')
r_stream_basins = Module('r.stream.basins')
v_in_ogr = Module('v.in.ogr')

r_in_gdal(input=drainDirPath,output='dir', o = True, overwrite = True, quiet = True) # bring in the drainage direction raster
g_region(raster = 'dir', res = 30) # set region resolution and extent
#r_external() # link the accumulation raster

v_in_ogr(input = '', output = 'gagues_fixed',)

# delineate all basins
r_stream_basins(direction = 'dir', points = 'gauges_fixed', basins = 'watersheds', mememory = 11800)

# iterate through each point and gather each upstream basin

watershed = garray.array()
watersheds.read('watersheds')

watershed = garray.array()

for cat,upstream in zip(gages.cat,gages.upstreamCats):
    upstream.extend(cat) # add the current cat label to the upstream labels.
    watershed[...] = np.zeros_like(watersheds)
    for cat in upstream:
        watershed[watersheds == cat] = 1 # set upstream values to 1

    watershed.write('watershed') # write out to GRASS

    # now convert to shapefile and export
    

for ID,x,y in zip(gauges.Gage_no,gauges.x,gauges.y):
    print('Starting Gauge No. %s in Region %s.'%(ID,reg))
    outfl = os.path.join(workspace,'gauges','region_%s_gageNo_%s_watershed_NHDplusV2_1.shp'%(reg,ID)) # format output string

    if os.path.isfile(outfl):
        print('Gauge No. %s in Region %s already complete.'%(ID,reg))
        continue

    else:
        cmd = 'echo \"%s|%s|%s\" > ./scratch/reg%s.tmp'%(1,x,y,reg)
        subprocess.call(cmd, shell=True) # send coordinates to text file

        # load the pour point
        v_in_ascii(input = './scratch/reg%s.tmp'%reg, output='pour', x=2, y=3, overwrite=True, quiet = True)

        # delineat the basin
        r_stream_basins(direction='dir',points='pour', basins='watershed', overwrite=True, quiet=True, memory=11800)

        #r_water_outlet(input = 'dir', output = 'watershed', coordinates =(x,y), overwrite=True, quiet = True) # delineate watershed
        r_to_vect(input = 'watershed', output = 'boundary', type = 'area', overwrite=True, quiet = True) # convert raster to vector

        # compute area of watershed
        v_db_addcol(map='boundary', columns='area_sqkm double precision', quiet = True)
        v_to_db(map='boundary', option='area', columns='area_sqkm', units='kilometers', quiet = True)

        v_out_ogr(e = True, input = 'boundary', type = 'area', output = outfl, overwrite=True, format = 'ESRI_Shapefile', quiet = True, c = True) # export the watershed boundary to a temporary file

        print('Gauge No. %s in Region %s complete.'%(ID,reg))
