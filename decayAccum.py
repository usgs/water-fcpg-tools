import os
import numpy as np
import rasterio as rs
import datetime
import subprocess
import traceback
from tools import *


def makeDecayGrid(d2strm, outRast):

    if not os.path.isfile(d2strm):
        print("Error - Flow direction raster file is missing!")
        return #Function will fail, so end it now


    with rs.open(d2strm) as ds: # load flow direction data
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata
        xsize, ysize = ds.res #Get flow direction cell size
    
    if xsize != ysize:
        print("Warning - grid cells are not square")


    outNoData = 0 #Set no data value for output raster

    print("Building multiplier grid {0}".format(datetime.datetime.now()))
    decayGrid = data.astype(np.float32) #Convert to float
    decayGrid[data == inNoData] = np.NaN # fill with no data values where appropriate
    decayGrid = 1/(decayGrid + xsize) #Add the resolution to every value and invert distances to streams

    decayGrid[np.isnan(decayGrid)] = outNoData # Replace numpy NaNs with no data value

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

        

def decayAccum(ang, mult, outRast, paramRast = None, cores=1) :

    if paramRast != None:
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
            print("Parameter accumulation written to: {0}".format(outRast))
                    
        except:
            print('Error Accumulating Data')
            traceback.print_exc()
    else:
        try:
            print('Accumulating parameter')
            tauParams = {
            'ang':ang,
            'cores':cores, 
            'dm':mult,
            'dsca': outRast,
            }
                    
            cmd = 'mpiexec -bind-to rr -n {cores} dinfdecayaccum -ang {ang} -dm {dm} -dsca {dsca}, -nc'.format(**tauParams) # Create string of tauDEM shell command
            print(cmd)
            result = subprocess.run(cmd, shell = True) # Run shell command
            result.stdout
            print("Parameter accumulation written to: {0}".format(outRast))
                
        except:
            print('Error Accumulating Data')
            traceback.print_exc()



def dist2stream(fdr, fac, thresh, outRast, cores=1) :


    try:
        print('Accumulating parameter')
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'fac':fac,
        'outRast': outRast,
        'thresh':thresh
        }
                
        cmd = 'mpiexec -bind-to rr -n {cores} d8hdisttostrm -p {fdr} -src {fac} -dist {outRast}, -thresh {thresh}'.format(**tauParams) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout
        print("Distance raster written to: {0}".format(outRast))
                
    except:
        print('Error computing distances')
        traceback.print_exc()


def make_Decaycpg(accumParam, fac, maskfac, outRast, noDataRast = None, minAccum = None):
    '''
    Inputs:
        
        accumParam - path to the accumulated parameter data raster
        fac - flow accumulation grid path
        outRast - output CPG file location
        noDataRast - raster of accumulated parameter no data values
        minAccum - Value of flow accumulation below which the CPG values will be set to no data
        

    Outputs:
        outRast - Parameter CPG 
    '''
    outNoData = -9999
    

    if not os.path.isfile(accumParam):
        print("Error - Accumulated parameter raster file is missing!")
        return #Function will fail, so end it now
    if not os.path.isfile(fac):
        print("Error - Flow accumulation file is missing!")
        return #Function will fail, so end it now


    print("Reading accumulated parameter file {0}".format(datetime.datetime.now()))
    with rs.open(accumParam) as ds: # load accumulated data and no data rasters
        data = ds.read(1)
        profile = ds.profile
        inNoData = ds.nodata

    data = data.astype(np.float32) #Convert to 32 bit float
    data[data == inNoData] = np.NaN # fill with no data values where appropriate

    print("Reading basin flow accumulation file {0}".format(datetime.datetime.now()))
    with rs.open(fac) as ds: # flow accumulation raster
        accum = ds.read(1)
        facNoData = ds.nodata # pull the accumulated area no data value


    if noDataRast != None:
        print("Correcting CPG for no data values")
        with rs.open(noDataRast) as ds: # accumulated no data raster
            accumNoData = ds.read(1)
            noDataNoData = ds.nodata # pull the accumulated no data no data value
            
        accumNoData[accumNoData == noDataNoData] = 0 #Set no data values to zero

        corrAccum = accum - accumNoData # Compute corrected accumulation
        corrAccum = corrAccum.astype(np.float32) # Convert to 32 bit float
        corrAccum[accum == facNoData] = np.NaN # fill with no data values where appropriate
        
    else:
        accum2 = accum.astype(np.float32)
        accum2[accum == facNoData] = np.NaN # fill this with no data values where appropriate
        corrAccum = accum2 # No correction required
        

    
    
    # Throw warning if there is a negative accumulation
    if np.nanmin(corrAccum) < 0:
        print("Warning: Negative accumulation value")
        print("Minimum value:{0}".format(np.nanmin(corrAccum)))
 
    print("Computing CPG values {0}".format(datetime.datetime.now()))
    dataCPG = data / (corrAccum + 1) # make data CPG

    print("Replacing numpy nan values {0}".format(datetime.datetime.now()))
    dataCPG[np.isnan(dataCPG)] = outNoData # Replace numpy NaNs with no data value

    # Replace values in cells with small flow accumulation with no data
    if minAccum != None:
        print("Replacing small flow accumulations {0}".format(datetime.datetime.now()))
        dataCPG[corrAccum < minAccum] = outNoData #Set values smaller than threshold to no data

    # Update raster profile
    profile.update({'dtype':dataCPG.dtype,
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'bigtiff':'IF_SAFER'})

    print("Saving CPG raster {0}".format(datetime.datetime.now()))
    with rs.open(outRast, 'w', **profile) as dst:
        dst.write(dataCPG,1)
        print("CPG file written to: {0}".format(outRast))
    
    


makeDecayGrid("../data/tauDEM/tauDist2Strm1002.tif", "../data/tauDEM/invDist1002.tif")

resampleParam("../data/cov/landsatNDVI/vrt/landsat_NDVI-May-Oct_2018_00_00.vrt", "../data/tauDEM/taufdr1002.tif", "../work/1002/landsat_NDVI-May-Oct_2018_00_00rprj.tif", resampleMethod="bilinear", cores=20)

decayAccum("../data/tauDEM/tauDINFang1002.tif",  "../data/tauDEM/invDist1002.tif", "../work/1002/paramdecayAccumTest.tif", paramRast="../work/1002/landsat_NDVI-May-Oct_2018_00_00rprj.tif", cores=20)

decayAccum("../data/tauDEM/tauDINFang1002.tif", "../data/tauDEM/invDist1002.tif", "../work/1002/decayAccumTest.tif", cores=20)

make_cpg("../work/1002/paramdecayAccumTest.tif", "../work/1002/decayAccumTest.tif", "../work/1002/decayAccumCPGTest.tif", minAccum = 40)


"""
HUCs = ["1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]

for HUC in HUCs:
    dist2stream("../data/tauDEM/taufdr{0}.tif".format(HUC), "../data/tauDEM/taufac{0}.tif".format(HUC), 1000, "../data/tauDEM/tauDist2Strm{0}.tif".format(HUC), cores=20)
"""