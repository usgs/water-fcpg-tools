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
import re

outFile = 'gridMET_minTempK_HUC1002_CPG.nc'


ds = gdal.Open('CPGs/gridMET_minTempK_1979_04_00_HUC1002_CPG.tif')
a = ds.ReadAsArray()
nlat,nlon = np.shape(a)

b = ds.GetGeoTransform() #bbox, interval
lon = np.arange(nlon)*b[1]+b[0]
lat = np.arange(nlat)*b[5]+b[3]


basedate = dt.datetime(1900,1,1,0,0,0) #Set basedate to January 1, 1900

# create NetCDF file
nco = netCDF4.Dataset(outFile,'w',clobber=True)

# chunking is optional, but can improve access a lot: 
# (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
chunk_lon=16
chunk_lat=16
chunk_time=12

# create dimensions, variables and attributes:
nco.createDimension('lon',nlon)
nco.createDimension('lat',nlat)
nco.createDimension('time',None)
timeo = nco.createVariable('time','f4',('time'))
timeo.units = 'days since 1858-11-17 00:00:00'
timeo.standard_name = 'time'

lono = nco.createVariable('lon','f4',('lon'))
lono.units = 'degrees_east'
lono.standard_name = 'longitude'

lato = nco.createVariable('lat','f4',('lat'))
lato.units = 'degrees_north'
lato.standard_name = 'latitude'

# create container variable for CRS: lon/lat WGS84 datum
crso = nco.createVariable('crs','i4')
csro.long_name = 'Lon/Lat Coords in WGS84'
crso.grid_mapping_name='latitude_longitude'
crso.longitude_of_prime_meridian = 0.0
crso.semi_major_axis = 6378137.0
crso.inverse_flattening = 298.257223563

# create short integer variable for temperature data, with chunking
tmno = nco.createVariable('tmn', 'i2',  ('time', 'lat', 'lon'), 
   zlib=True,chunksizes=[chunk_time,chunk_lat,chunk_lon],fill_value=-9999)
tmno.units = 'degC'
tmno.scale_factor = 0.01
tmno.add_offset = 0.00
tmno.long_name = 'minimum monthly temperature'
tmno.standard_name = 'air_temperature'
tmno.grid_mapping = 'crs'
tmno.set_auto_maskandscale(False)

nco.Conventions='CF-1.6'

#write lon,lat
lono[:]=lon
lato[:]=lat

pat = re.compile('us_tmin_[0-9]{4}\.[0-9]{2}')
itime=0

#step through data, writing time and data to NetCDF
for root, dirs, files in os.walk('/usgs/data0/prism/1890-1899/'):
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