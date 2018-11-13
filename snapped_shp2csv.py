import geopandas as gpd
import pandas as pd
import sys

reg = sys.argv[1] # pull the region

snapped = gpd.read_file('./data/CATCHMENT_region_%s_fixed.shp'%(reg)) # load the corrected shapefile
IDvals = pd.read_csv('./data/CATCHMENT_reg_%s_snapped_ID.csv'%(reg)) # load a file to relate cats to gaugeID

# clean the gaugeID file
del IDvals['x']
del IDvals['y']
del IDvals['Unnamed: 0']
del IDvals['Unnamed: 0.1']

def get_xy(df): # function to extract coordinates from shapefile
    return df.geometry.centroid.x,df.geometry.centroid.y

res = snapped.apply(get_xy,axis=1)
x,y = zip(*res)
snapped['x'] = x
snapped['y'] = y
del snapped['geometry']

outDF = pd.merge(left = snapped, right = IDvals, on = 'cat')

outDF.to_csv('./data/CATCHMENT_region_%s_snapped_fixed.csv'%(reg), index=False, index_label=None, header=True)