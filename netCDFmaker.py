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
import os
import gdal
import netCDF4
#import re

outFile = '../CPGs/nc/gridMET_minTempK_HUC1002_CPG.nc'
netCDFparam = 'gridMET_minTempK'
inDir = "../CPGs/1002"
templateFile = '../CPGs/1002/gridMET_minTempK_1979_04_00_HUC1002_CPG.tif'

ds = gdal.Open(templateFile)
a = ds.ReadAsArray()
nx,ny = np.shape(a)

b = ds.GetGeoTransform() #bbox, interval
y = np.arange(ny)*b[1]+b[0]
x = np.arange(nx)*b[5]+b[3]


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
nco.createDimension('lon', nx)
nco.createDimension('lat', ny)
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
y = nco.createVariable('y','f4',('y'))
y.units = 'm'
y.standard_name = 'projection_y_coordinate'

x = nco.createVariable('x','f4',('x'))
x.units = 'm'
x.standard_name = 'projection_x_coordinate'

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
crso.grid_mapping_name='albers_conical_equal_area_usgs_version'
crso.standard_parallel_1 = 29.5
crso.standard_parallel_2 = 45.5
crso.latitude_of_projection_origin = 23.0
crso.longitude_of_central_meridian = -96.0
crso.false_easting = 0
crso.false_northing = 0
crso.semi_major_axis = 6378137.0
crso.inverse_flattening = 298.257222101

# create short integer variable for temperature data, with chunking
#Use 32 bit unsigned integer (u4)
tmno = nco.createVariable('tmn', 'u4',  ('time', 'y', 'x'), zlib=True,fill_value=999) #Create variable, compress with gzip (zlib=True)
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

#step through data, writing time and data to NetCDF
for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file hs correct parameter name
        baseName = os.path.splitext(name)[0]
        source = baseName.split("_")[0]
        param = baseName.split("_")[1]

        if source + "_" + param == netCDFparam:
           year = int(baseName.split("_")[2])
           month = int(baseName.split("_")[3])
           day = int(baseName.split("_")[4])
           
           #Set months or days that are zero to one
           if month == 0:
              month = 1
           if day == 0:
              day = 1


           CPGfile = os.path.join(path, name)
           print(CPGfile)
           #HUC = baseName.split("_")[5]
           date = dt.datetime(year, month, day, 0, 0, 0)
           dtime=(date-basedate).total_seconds()/86400.
           timeo[itime]=dtime
           cpgTiff = gdal.Open(CPGfile)
           a=cpgTiff.ReadAsArray()  #data
           print(tmno)
           tmno[itime,:,:]=a
           itime=itime+1

nco.close()



"""
for root, dirs, files in os.walk('/CPGs/'):
    dirs.sort()
    files.sort()
    for f in files:
        if re.match(pat,f):
            # read the time values by parsing the filename
            year=int(f[8:12])
            mon=int(f[13:15])
            date=dt.datetime(year,mon,1,0,0,0)
            print(date)
            dtime=(date-basedate).total_seconds()/86400.
            timeo[itime]=dtime
           # min temp
            tmn_path = os.path.join(root,f)
            print(tmn_path)
            tmn=gdal.Open(tmn_path)
            a=tmn.ReadAsArray()  #data
            tmno[itime,:,:]=a
            itime=itime+1

nco.close()
"""