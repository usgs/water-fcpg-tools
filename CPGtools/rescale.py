# Script to rescale raster data
#
# Theodore Barnhart
# tbarnhart@usgs.gov

import sys
import rasterio as rs
import numpy as np

infl = sys.argv[1] # input filename
outfl = sys.argv[2] # output filename
srcND = float(sys.argv[3]) # no data value
scale = float(sys.argv[4])

print('Reading %s'%infl)
with rs.open(infl,'r') as src:
    dat = src.read(1)
    profile = src.profile

print('Altering %s to np.NaN'%srcND)
dat.dtype=np.float64 # change data type
dat[dat==srcND] = np.NaN

print('Rescaling data by %s'%scale)
dat = dat/scale

profile.update({'dtype':'float64',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS'}) # update geotiff profile with creation options.

print('Writing output to %s'%outfl)
with rs.open(outfl, 'w', **profile) as dst:
    dst.write(dat,1)