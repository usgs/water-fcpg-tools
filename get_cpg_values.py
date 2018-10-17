from __future__ import print_function #python 2/3
import pandas as pd
import glob
import sys
import gdal

reg = sys.argv[1] # pull the region from the command line arguments

def get_val(dat,gt=[],rb=[]):
    ''' Grab cell value based on data frame x and y variables.
    dat = dataframe containing x and y 
    gt = geotransform, of the index raster
    rb = raster band to pick data from
    '''
    mx = dat.x
    my = dat.y
    # transform to array coordinates
    px = int((mx-gt[0])/gt[1]) # x pixle
    py = int((my-gt[3])/gt[5]) # y pixle
    
    # extract the value
    intval = rb.ReadAsArray(px,py,1,1)
    return intval[0][0]

cpgs = glob.glob('./data/cpg_datasets/output_cpg/*_%s_cpg.tiff'%(reg)) # pull a list of cpgs

dat = pd.read_csv('./data/CATCHMENT_region_%s.csv'%(reg)) # load the dataset

for fl in cpgs: # iterate through each CPG
    CPG = fl.split('/')[-1].split('_%s'%reg)[0] # get CPG name

    src_ds = gdal.Open(fl)
    gt = src_ds.GetGeoTransform() # extract geotransform
    rb = src_ds.GetRasterBand(1) # extract raster band

    dat[CPG] = dat.apply(get_val,gt=gt,rb=rb,axis=1) # query the maps
    print('Completed %s'%CPG)

outfl = './data/CATCHMENT_cpgDat_reg_%s.csv'%(reg)
print('Writing output to: %s'%(outfl))
dat.to_csv(outfl,index=False,header=True,index_label=False)
print('Done!')