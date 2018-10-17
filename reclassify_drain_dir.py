import rasterio as rs
import numpy as np
import sys
import os

reg = sys.argv[1] # first command line argument
workingDir = '/home/tbarnhart/projects/DEM_processing/data/NHDplusV21_facfdr' # working directory
inRast = os.path.join(workingDir,'region_%s_fdr.vrt'%(reg)) # input raster path creation
outRastTau = os.path.join(workingDir,'region_%s_fdr_tau.tiff'%(reg)) # tauDEM reclassified raster
outRastGRASS = os.path.join(workingDir,'region_%s_fdr_grass.tiff'%(reg)) # GRASS reclassified raster

print('Reclassifying Region %s'%reg)

# load input data
with rs.open(inRast) as ds:
    dat = ds.read(1)
    meta = ds.meta.copy() # save the metadata for output later

# edit the metadata
meta.update({'driver':'GTiff'})

#print(meta)

tauDir = dat.copy()
# remap NHDplus flow direction to TauDEM flow Direction
# east is ok
tauDir[dat == 2] = 8 # stauDirheast
tauDir[dat == 4] =  7 # stauDirh
tauDir[dat == 8] = 6 # stauDirhwest
tauDir[dat == 16] = 5 # west
tauDir[dat == 32] = 4 # northwest
tauDir[dat == 64] = 3 # north
tauDir[dat == 128] = 2 # northeast

#print(np.shape(tauDir))

with rs.open(outRastTau,'w',**meta) as dst:
    dst.write(tauDir,1)

print('TauDEM drainage direction written to: %s'%outRastTau)

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

with rs.open(outRastGRASS,'w',**meta) as dst:
    dst.write(grassDir,1)

print('GRASS drainage direction written to: %s'%outRastGRASS)