import glob
import pandas as pd
import numpy as np

def fixRegion(df):
    reg = df.NHDPlusReg
    
    if reg[:2] == '03':
        reg = '03'
        
    if reg[:2] == '10':
        reg = '10'
    
    return reg

def createFileName(df):
    fn = 'region_%s_gageNo_%s_watershed_NHDplusV2_1.shp'%(df.NHDPlusReg,df.Gage_no)
    return fn

def getRegion(fileName):
    return fileName.split('_')[1]

def splitFilename(fileName):
    return fileName.split('/')[-1] # carve off the last part of the filename

gages = pd.read_csv('./data/CATCHMENT_v1.csv') # read all the gauges

compGages = pd.DataFrame()
compGages['fileName'] = glob.glob('./data/gauges/*.shp') # grab the shapefiles

# clean the gauges
gages.loc[gages.Lat_snap == -9999,'Lat_snap'] = np.NaN
gages.loc[gages.Long_snap == -9999,'Long_snap'] = np.NaN
gages.dropna(inplace=True)

gages.NHDPlusReg = gages.apply(fixRegion, axis = 1)
gages['fileName'] = gages.apply(createFileName, axis = 1)

compGages['Reg'] = compGages.fileName.map(getRegion) # get regions from filenames
compGages['fileName'] = compGages.fileName.map(splitFilename) # split off end of filename

missing = []

for reg in range(1,19):

    # convert indexer to padded string
    reg = str(reg)
    reg = reg.zfill(2)

    allGages = list(gages.loc[gages.NHDPlusReg == reg].fileName.values)
    haveGages = list(compGages.loc[compGages.Reg == reg].fileName.values)
    needGages = list(set(allGages) - set(haveGages)) # compute the needed dates
    print('Region %s: %s Missing. Ratio: %s/%s'%(reg,len(needGages),len(haveGages), len(allGages)))
    missing.append(len(needGages))