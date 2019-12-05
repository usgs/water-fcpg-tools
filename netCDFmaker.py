'''
Based on code from Rich Signell
Convert a bunch of GDAL readable grids to a NetCDF Time Series.
Here we read a bunch of files that have names like:
CPGs/gridMET_minTempK_1979_04_00_HUC1002_CPG.tif
CPGs/gridMET_minTempK_1979_05_00_HUC1002_CPG.tif
...
CPGs/gridMET_minTempK_1980_04_00_HUC1002_CPG.tif
'''

import numpy as np
import datetime as dt
import rasterio as rs
import os
import netCDF4
import sys
import glob
import time

strt = dt.datetime.now()

#inDir = sys.argv[1]
#netCDFparam = sys.argv[2]
#outFile = sys.argv[3]


outFile = 'data/gridMET_minTempK_HUC1003_CPG.nc'
netCDFparam = 'gridMET_minTempK'
inDir = "data/cpgs_to_netCDF/*.tif"
cl = 9

metaDict = {
  'title':'',
  'institution':'',
  'source':'',
  'references':'',
  'comment':'',
  'var_name':'Tmin',
  'units':'K',
  'add_offset':0.0,
  'standard_name':'min_temperature',
  'long_name':'minimum monthly temperature',
  'grid_mapping':'crs'
  'scale_factor':1.0
}

# enforce some defaults if they are not present
if 'conventions' not in metaDict.keys():
  metaDict['conventions'] = 'CF-1.7'

if 'grid_mapping' not in metaDict.keys():
  metaDict['']

files = glob.glob(inDir) # there probably should be some more work here to parse time and order the files by time so that the loop works properly at the end.

assert len(files) > 0 # check that there are files to process
templateFile = files [0] # use first file as the template

np.set_printoptions(threshold=sys.maxsize)

with rs.open(templateFile) as ds:
   NoData = ds.nodata
   dataType = ds.dtypes[0] #Get datatype of first band
   xsize, ysize = ds.res #Get  cell size
   
   #Get bounding coordinates of the raster
   Xmin = ds.transform[2]
   Ymax = ds.transform[5]
   Xmax = Xmin + xsize*ds.width
   Ymin = Ymax - ysize*ds.height
   
   a = ds.transform
   nrow,ncol = ds.shape

# make arrays of rows and columns
nx = np.arange(ncol)
ny = np.arange(nrow)
print("Grid Shape:")
print("\tncol:",ncol)
print("\tnrow:",nrow)

# translate the rows and columns to x,y
x,tmp = rs.transform.xy(rows = np.repeat(0,len(nx)),cols = nx, transform=a)
tmp,y = rs.transform.xy(rows = ny, cols = np.repeat(0,len(ny)), transform=a)
del tmp

print("\tx:",len(x))
print("\ty:",len(y))

print(dataType)
if dataType == 'float32':
   ncDataType = 'f4'
elif dataType == 'int32':
   ncDataType = 'i4'

basedate = dt.datetime(1900,1,1,0,0,0) #Set basedate to January 1, 1900

# create NetCDF file
nco = netCDF4.Dataset(outFile,'w',clobber=True)
nco.Conventions=metaDict['conventions']

# chunking is optional, but can improve access a lot: 
# (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
#chunk_lon=16
#chunk_lat=16
#chunk_time=12

# create dimensions, variables and attributes:
nco.createDimension('y',nrow)
nco.createDimension('x',ncol)
nco.createDimension('time', None)

# time axis
timeo = nco.createVariable('time','f4',('time'))
timeo.units = 'days since 1900-01-01 00:00:00'
timeo.standard_name = 'time'

# projected vertical coordinates (latitude)
yo = nco.createVariable('y','f4',('y'),zlib=True, complevel=cl, shuffle = True)
yo.units = 'm'
yo.standard_name = 'projection_y_coordinate'

# projected horizontal coordinates (longitude)
xo = nco.createVariable('x','f4',('x'),zlib=True, complevel=cl, shuffle = True)
xo.units = 'm'
xo.standard_name = 'projection_x_coordinate'

#write lon,lat
xo[:]=x
yo[:]=y

#Define coordinate system for Albers Equal Area Conic USGS version
'''
Should we make this a dictionary so / automatically create this from the input files?
'''
crso = nco.createVariable('crs','i4') #i4 = 32 bit signed int
crso.grid_mapping_name='albers_conical_equal_area'
#crso.standard_parallel_1 = 29.5
#crso.standard_parallel_2 = 45.5
crso.standard_parallel = [45.5, 29.5]
crso.latitude_of_projection_origin = 23.0
crso.longitude_of_central_meridian = -96.0
crso.false_easting = 0
crso.false_northing = 0
crso.semi_major_axis = 6378137.0
crso.inverse_flattening = 298.257222101
crso.unit = 'm'
wkt = 'PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",GEOGCS[\"GCS_North_American_1983\",DATUM[\"D_North_American_1983\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-96.0],PARAMETER[\"Standard_Parallel_1\",29.5],PARAMETER[\"Standard_Parallel_2\",45.5], PARAMETER[\"Latitude_Of_Origin\",23.0], UNIT[\"Meter\",1]]'
crso.crs_wkt = wkt
crso.spatial_ref = wkt
'''
We might need to implement the metadata here by passing the script a dictionary...

We should also look to see if we can make the netCDF ISO 19115 compliant so that we can put these bad boys on sciencebase.
'''


# create short integer variable for temperature data, with chunking
tmno = nco.createVariable(metaDict['var_name'], ncDataType,  ('time', 'y', 'x'), zlib=True, fill_value=NoData, complevel=cl, shuffle = True) #Create variable, compress with gzip (zlib=True)
tmno.units = metaDict['units']
tmno.scale_factor = metaDict['scale_factor']
tmno.add_offset = metaDict['add_offset']
tmno.long_name = metaDict['long_name']
tmno.standard_name = metaDict['standard_name']
tmno.grid_mapping = metaDict['grid_mapping']
tmno.set_auto_maskandscale(False)

itime=0
for name in sorted(files):
  #Check if file has correct parameter name
  baseName = name.split('/')[-1]
  source = baseName.split("_")[0]
  param = baseName.split("_")[1]

  if source + "_" + param == netCDFparam: # test if netCDF file is correct.
    print(name)
    year = int(name.split('/')[-1].split('_')[-5])
    month = int(name.split('/')[-1].split('_')[-4])
    day = int(name.split('/')[-1].split('_')[-3])
    #print(year,month,day)
    date = dt.datetime(year, month, day+1, 0, 0, 0) # set base date
    dtime=(date-basedate).total_seconds()/86400.
    timeo[itime]=dtime

    #Try reading with rasterio
    with rs.open(name) as ds: # load accumulated data and no data rasters
      #data = ds.read(1)
      #print(np.shape(data))
      #print(np.shape(tmno[itime,:,:]))
      tmno[itime,:,:] = ds.read(1)

    itime=itime+1

nco.close()

print((dt.datetime.now()-strt))