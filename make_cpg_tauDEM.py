import numpy as np
import pandas as pd
import gdal
import subprocess
import sys
import glob
import rasterio as rs
import os
import shutil

reg = sys.argv[1] # pull the region
jobID = sys.argv[2] # pull the slurm job ID
cores = int(sys.argv[3]) - 1 # pull the number of cores available

fdrPath = './data/NHDplusV21_facfdr/region_%s_fdr_tau.tiff'%(reg) # path to the flow direction raster
facPath = './data/NHDplusV21_facfdr/region_%s_fac.vrt'%(reg)
tempDir = './data/temps/%s'%(jobID)
outDir = './data/cpg_datasets/output_cpg'
paramPath ='./data/cpg_datasets/' # load all tiff files from this path

#gdalDataTypes = {
#    'ditches92':'Byte', # percent
#    'lu2012':'Byte', # percent
#    'mirad1k':'Byte', # percent
#    'mirad250':'Byte', # percent
#    'nid_normstorage':'Float32',
#    'nid_storage':'Float32',
#    'nlcd_2011_imperv':'Byte', # percent
#    'npd_occur':'Byte', # dams per grid cell
#    'ppt7100':'Float32', 
#    'withdr1k':'Float32'
#}


def make_cpg(param,dataPath,noDataPath,tempDir=tempDir,facPath=facPath,outDir = outDir, reg = reg):
    '''
    Inputs:
        param - parameter name that output filenames are based off of
        dataPath - path to the accumulated parameter data raster
        noDataPath - path to the accumulated no data raster
        tempDir - temperary direcotyr, Default: tempDir variable defined above
        facPath - flow accumulation grid path, Default: facPath variable defined above
        outDir - output directory, Default: outDir variable defined above
        reg - region, Default: reg variable defined above 

    Outputs:
        Parameter and NoData CPGS as bands 1 and 2 of a file in the output directory.
    '''
    outNoData = -9999
    CPGpath = os.path.join(outDir,param+'_%s_cpg.tiff'%(reg))

    with rs.open(dataPath) as ds: # load accumulated data and no data rasters
        data = ds.read(1)
        profile = ds.profile

    with rs.open(noDataPath) as ds:
        noData = ds.read(1)

    with rs.open(facPath) as ds: # flow accumulation raster
        accum = ds.read(1)
        accumNoData = ds.nodata # pull the accumulated area no data value

    accum2 = accum.astype(np.float32)
    accum2[accum == accumNoData] = np.NaN # fill this with no data values where appropriate
    
    # zero negative accumulations
    accum[accum < 0] = 0 
    noData[noData < 0] = 0
    data[data < 0] = 0

    corrAccum = (accum - noData) # compute corrected accumulation
    addition = np.min(corrAccum) # find the minumum value, since the denominator cannot be zero

    if addition > 0: # if the minumum value is positive, make addition zero
        addition = 1
    else: # otherwise, make the addition the absolute value of the minimim to bring the corrAccum min to + 1
        addition = np.abs(addition) + 1

    dataCPG = data / (corrAccum + addition) # make data CPG, correct for negative values if any
    
    noDataCPG = noData / (corrAccum + addition) # make noData CPG

    # fill edges with no data, not sure this is the correc thing to do.
    dataCPG[np.isnan(accum2)] = outNoData
    noDataCPG[np.isnan(accum2)] = outNoData

    profile.update({'dtype':dataCPG.dtype,
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':outNoData,
                'count':2})

    with rs.open(CPGpath, 'w', **profile) as dst:
        dst.write(dataCPG,1)
        dst.write(noDataCPG,2)

    return None

def fill_noData(df,append=[],fillVal=[],tempDir=tempDir):
    '''
    Inputs:
        df - data frame with paths to data rasters (string) and parameter names:
            df.name - assumed name of parameter names
            df.sourcePath - assumed name of data raster path
        append - string to append to the parameter name
        fillVal - value to fill raster NoData values with, zero or 1 (int)
        tempDir - temporary directory, defined above.
    Outputs:
        fillPath - path to the filled raster
    '''
    #try:
    param = df['name']
    path = df.sourcePath
    fillPath = os.path.join(tempDir,param+'_%s.tiff'%(append))

    noDataOut = 0

    with rs.open(path) as ds: # read data
        dat = ds.read(1) # let the driver dictate the data type
        profile = ds.profile
        noData = ds.nodata

    dat[dat==noData] = 0 # make noData values zero
    dat[dat<= 0] = 0 # make weird fill values zero
    noDataOut = -9999

    if fillVal == 1:
        outDat = np.zeros_like(dat, dtype = np.uint8) # make binary copy raster
        outDat[:] = 1 # fill with ones
        outDat[dat != 0] = 0 # dat raster values not equal to zero are filled with zeros in the binary raster

        dat = outDat # copy the output raster back to the data raster
        del outDat
        noDataOut = 255

    # update geoTiff profile
    profile.update({'dtype':dat.dtype,
                    'compress':'LZW',
                    'profile':'GeoTIFF',
                    'tiled':True,
                    'sparse_ok':True,
                    'num_threads':'ALL_CPUS',
                    'nodata':noDataOut})

    with rs.open(fillPath, 'w', **profile) as dst: # write out the dataset
        dst.write(dat,1)

    return fillPath
    #except:
    #    print('Error Filling.')
    #    return None

# create temp directory
os.mkdir(tempDir)

# check that all the input and outputs exist
assert os.path.isfile(fdrPath) == True
assert os.path.isfile(facPath) == True
assert os.path.isdir(tempDir) == True
assert os.path.isdir(outDir) == True
assert os.path.isdir(paramPath) == True

params = pd.DataFrame()
params['path'] = glob.glob(os.path.join(paramPath,'*.tiff'))[0:1] #list the source datasets

def get_param_name(path):
    name = path.split('.tiff')[0].split('/')[-1]
    print(name)
    return name

params['name'] = params.path.map(get_param_name) # extract parameter names

# get regional raster extent
xmins = []
xmaxs = []
ymins = []
ymaxs = []

for rast in [fdrPath,facPath]: # extract min and max raster bounds
    with rs.open(rast) as ds:
        xmins.append(ds.bounds[0])
        xmaxs.append(ds.bounds[2])
        ymins.append(ds.bounds[1])
        ymaxs.append(ds.bounds[3])

# summarize the extents to the largest possible
xmin = np.max(xmins)
xmax = np.min(xmaxs)
ymin = np.max(ymins)
ymax = np.min(ymaxs)

# test that raster extents are equal
for rast in [fdrPath,facPath]:
    with rs.open(rast) as ds:
        assert xmin == ds.bounds[0], "Regional Extents Not Equal"
        assert xmax == ds.bounds[2], "Regional Extents Not Equal"
        assert ymin == ds.bounds[1], "Regional Extents Not Equal"
        assert ymax == ds.bounds[3], "Regional Extents Not Equal"

cropParams = {
    'xmin':xmin,
    'xmax':xmax,
    'ymin':ymin,
    'ymax':ymax,
    't_srs':'EPSG:42303'
}

outPaths = []
for param,path in zip(params.name,params.path): # crop input datasets to common extents
    try:
        # update input and output files:
        cropParams['inFl'] = path
        cropParams['outFl'] = os.path.join(tempDir,param+'.tiff') # create temp output file

        print('Cropping %s to temporary directory.'%(param))
        cmd = 'gdalwarp -wo NUM_THREADS=ALL_CPUS -co TILED=YES -co COMPRESS=LZW -co NUM_THREADS=ALL_CPUS -co SPARSE_OK=TRUE -co PROFILE=GeoTIFF -multi -tr 30 30 -te {xmin} {ymin} {xmax} {ymax} {inFl} {outFl}'.format(**cropParams)
        subprocess.call(cmd, shell = True)
        outPaths.append(cropParams['outFl']) # save the output path
    except:
        print('Error cropping %.'%(param))
        outPaths.append(None)

params['sourcePath'] = outPaths # update output paths into the dataframe

# generate no data rasters with no-data filled to 1
params['noDataPath'] = params.apply(fill_noData,axis = 1, append = 'noData', fillVal = 1)

# generate data rasters with no-data filled to 0
params['dataPath'] = params.apply(fill_noData,axis = 1, append = 'zeroFill', fillVal = 0)

# TauDEM code
tauParams = {
    'fdr':fdrPath,
    'cores':cores
}

# TauDEM accumulation
outPathsData = []
outPathsNoData = []
for param,dataPath,noDataPath in zip(params.name, params.dataPath, params.noDataPath): 
    # first accumulate the parameter
    try:
        print('Accumulating Data %s'%param)
        tauParams['outFl'] = os.path.join(tempDir,param+'_fill_accum.tiff')
        tauParams['weight'] = dataPath
        
        cmd = 'mpiexec -n {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight}' -nc.format(**tauParams)
        subprocess.call(cmd, shell = True)
        outPathsData.append(tauParams['outFl']) # save accumualted data path
    except:
        print('Error Accumulating Data')
        outPathsData.append(None)

    # now accumulate the no data values
    try:
        print('Accumulating NoData %s'%param)
        # then accumualte the noData binary grid
        tauParams['outFl'] = os.path.join(tempDir,param+'_noData_accum.tiff')
        tauParams['weight'] = noDataPath

        cmd = 'mpiexec -n {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams)
        print(cmd)
        subprocess.call(cmd, shell = True)
        outPathsNoData.append(tauParams['outFl']) # save accumulated no data path
    except:
        print('Error Accumulating NoData')
        outPathsNoData.append(None)

# save the output paths
params['accumData'] = outPathsData
params['accumNoData'] = outPathsNoData

for param,dataPath,noDataPath in zip(params.name, params.accumData, params.accumNoData):
    #try:
    print('Computing CPGS for %s'%(param))
    make_cpg(param,dataPath,noDataPath)
    #except:
    #    print('Error Computing CPGS for %s'%(param))

# delete the temp dir
#shutil.rmtree(tempDir)