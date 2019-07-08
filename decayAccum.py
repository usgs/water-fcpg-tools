import os
import numpy as np
import rasterio as rs
import datetime
import subprocess
import traceback



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

        

def decayAccum(ang, paramRast, mult, outRast, cores=1) :


    try:
        print('Accumulating parameter')
        tauParams = {
        'ang':ang,
        'cores':cores, 
        'dm':mult,
        'dsca': outRast,
        'weight':paramRast
        }
                
        cmd = 'mpiexec -bind-to rr -n {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout
        print("Parameter no data accumulation written to: {0}".format(outNoDataRast))
                
    except:
        print('Error Accumulating Data')
        traceback.print_exc()


#makeDecayGrid("../data/tauDEM/taufdr1002.tif", 0.5, "../data/tauDEM/mult1002.tif")

decayAccum("../data/tauDEM/tauDINFang1002.tif", "../data/cov/SNODAS_SWEmm/SNODAS_SWEmm_2004_03_01.tif", "../data/tauDEM/mult1002.tif", "../data/cov/decayAccumTest.tif")