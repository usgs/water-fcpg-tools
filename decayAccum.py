import os
import numpy as np
import rasterio as rs
import datetime



def makeDecayGrid(fdr, multiplier, outRast):

    if not os.path.isfile(fdr):
        print("Error - Flow direction raster file is missing!")
        return #Function will fail, so end it now


    with rs.open(fdr) as ds: # load flow direction data
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata

    print("Building multiplier grid {0}".format(datetime.datetime.now()))
    decayGrid = data.astype(np.float32) #Convert to float
    decayGrid[data != inNoData] = multiplier # fill all data cells with with multiplier values


    # Update raster profile
    profile.update({
                'dtype': decayGrid.dtype,
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':inNoData,
                'bigtiff':'IF_SAFER'})

    print("Saving decay raster {0}".format(datetime.datetime.now()))
    
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(decayGrid,1)
        print("Decay raster written to: {0}".format(outRast))

        

    


makeDecayGrid("../data/tauDEM/taufdr1002.tif", 0.5, "../data/tauDEM/mult1002.tif")