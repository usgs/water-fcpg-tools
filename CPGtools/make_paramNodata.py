from __future__ import print_function #python 2/3
import rasterio as rs
import numpy as np
import sys

inFile = sys.argv[1] # input data file
outFile = sys.argv[2] # output data file

print('Opening %s'%inFile)
with rs.open(inFile) as ds:
    dat = ds.read(1) # pull the first band
    noData = ds.nodata # grab the no data value
    params = ds.profile

print('Converting NoData Values.')
dat[dat!=noData] = 0 # make data values zero
dat[dat==noData] = 1 # make noData values 1 to be accumulated later

dat.dtype = np.uint8 # byte data type

print('Updating profile.')
# update geotiff profile 
params.update({'dtype':'byte',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':255})

print('Writing output to %s'%outfl)
with rs.open(outFile,'w',**profile) as dst:
    dst.write(dat,1)
