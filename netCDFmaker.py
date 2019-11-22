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
import gdal
import netCDF4
import sys
#import re

np.set_printoptions(threshold=sys.maxsize)

outFile = '../CPGs/nc/gridMET_minTempK_HUC1002_CPG.nc'
netCDFparam = 'gridMET_minTempK'
inDir = "../CPGs/nc/testInput"
templateFile = '../CPGs/nc/testInput/gridMET_minTempK_1979_01_00_HUC1002_CPG.tif'

ds = gdal.Open(templateFile)
a = ds.ReadAsArray()
nx,ny = np.shape(a)

b = ds.GetGeoTransform() #bbox, interval
y = np.arange(ny)*b[5]+b[3]
x = np.arange(nx)*b[1]+b[0]

#Get raster no data value 
with rs.open(templateFile) as ds:
   data = ds.read(1)
   NoData = ds.nodata
   dataType = ds.dtypes[0] #Get datatype of first band
   xsize, ysize = ds.res #Get  cell size
   #Get bounding coordinates of the raster
   Xmin = ds.transform[2]
   Ymax = ds.transform[5]
   Xmax = Xmin + xsize*ds.width
   Ymin = Ymax - ysize*ds.height

   #nx,ny = nx,ny = np.shape(data)
   #y = np.arange(ny)*ds.transform[5]+ds.transform[3]
   #x = np.arange(nx)*ds.transform[1]+ds.transform[0]



print(dataType)
if dataType == 'float32':
   ncDataType = 'f4'
elif dataType == 'int32':
   ncDataType = 'i4'

basedate = dt.datetime(1900,1,1,0,0,0) #Set basedate to January 1, 1900

# create NetCDF file
nco = netCDF4.Dataset(outFile,'w',clobber=True)

# chunking is optional, but can improve access a lot: 
# (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
#chunk_lon=16
#chunk_lat=16
#chunk_time=12

# create dimensions, variables and attributes:
nco.createDimension('y',ny)
nco.createDimension('x',nx)
#nco.createDimension('lon', nx)
#nco.createDimension('lat', ny)
nco.createDimension('time', None)
timeo = nco.createVariable('time','f4',('time'))
timeo.units = 'days since 1900-01-01 00:00:00'
timeo.standard_name = 'time'

"""
lono = nco.createVariable('lon','f4',('lon'))
lono.units = 'degrees_east'
lono.standard_name = 'longitude'

lato = nco.createVariable('lat','f4',('lat'))
lato.units = 'degrees_north'
lato.standard_name = 'latitude'
"""
yo = nco.createVariable('y','f4',('y'))
yo.units = 'm'
yo.standard_name = 'projection_y_coordinate'

xo = nco.createVariable('x','f4',('x'))
xo.units = 'm'
xo.standard_name = 'projection_x_coordinate'

"""
# create container variable for CRS: lon/lat WGS84 datum
crso = nco.createVariable('crs','i4')
csro.long_name = 'Lon/Lat Coords in WGS84'
crso.grid_mapping_name='latitude_longitude'
crso.longitude_of_prime_meridian = 0.0
crso.semi_major_axis = 6378137.0
crso.inverse_flattening = 298.257223563
"""

#Define coordinate system for Albers Equal Area Conic USGS version
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
crso.crs_wkt = 'PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",GEOGCS[\"GCS_North_American_1983\",DATUM[\"D_North_American_1983\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-96.0],PARAMETER[\"Standard_Parallel_1\",29.5],PARAMETER[\"Standard_Parallel_2\",45.5], PARAMETER[\"Latitude_Of_Origin\",23.0], UNIT[\"Meter\",1]]'

# create short integer variable for temperature data, with chunking
tmno = nco.createVariable('tmn', ncDataType,  ('time', 'y', 'x'), zlib=True, fill_value=NoData) #Create variable, compress with gzip (zlib=True)
tmno.units = 'K'
#tmno.scale_factor = 0.01
tmno.add_offset = 0.00
tmno.long_name = 'minimum monthly temperature'
tmno.standard_name = 'min_temperature'
tmno.grid_mapping = 'crs'
tmno.set_auto_maskandscale(False)

nco.Conventions='CF-1.6'

#write lon,lat
xo[:]=x
yo[:]=y

itime=0

#Test code for static rasters
for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file hs correct parameter name
        baseName = os.path.splitext(name)[0]
        source = baseName.split("_")[0]
        param = baseName.split("_")[1]

        if source + "_" + param == netCDFparam:


           CPGfile = os.path.join(path, name)
           print(CPGfile)
           #HUC = baseName.split("_")[5]
           date = dt.datetime(1900, 1, 1, 0, 0, 0)
           dtime=(date-basedate).total_seconds()/86400.
           timeo[itime]=dtime

           """
           cpgTiff = gdal.Open(CPGfile)
           a=cpgTiff.ReadAsArray()  #data
           tmno[itime,:,:]=a
           """
           #Try reading with rasterio
           with rs.open(CPGfile) as ds: # load accumulated data and no data rasters
              data = ds.read(1)
              print(np.shape(data))
              print(np.shape(tmno[itime,:,:]))
              tmno[itime,:,:] = np.flipud(np.transpose(data))


           itime=itime+1


nco.close()

