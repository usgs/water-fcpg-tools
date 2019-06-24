import rasterio as rs
import numpy as np
import datetime
import os
import subprocess
import traceback

# Script to destroy the netCDF file Roy got from gridMET
# Must have gdal and nco tools (module load tools/nco-4.7.8-gnu) modules loaded 

inCDF = "../data/cov/minTempNCDF/tmmn_1994.nc" #Original netCDF from gridMET
reorderCDF = "../data/cov/minTempNCDF/tmmn_1994fix.nc" #NetCDF file with reordered dimensions
multiTIFF = "../data/cov/minTempNCDF/tmmn_1994.tif" #Multiband .tif created from netCDF

baseName = "gridMET_minTempK"

outDir = "../data/cov/gridMET_minTempK"

year = os.path.splitext(os.path.basename(inCDF))[0].split("_")[1] # Get year from input file


#Step 1: Put the file dimensions in the correct order

try:
        cmd = "ncpdq -a day,lat,lon,crs {0} {1}".format(inCDF, reorderCDF)
        result = subprocess.run(cmd, shell = True)
        result.stdout
        
except:
        print('Error reordering NetCDF dimensions')
        traceback.print_exc()


#Step 2: Convert the netCDF to a multiband GeoTIFF


try:
        cmd = "gdal_translate -of GTiff -a_srs EPSG:4326 {0} {1}".format(reorderCDF, multiTIFF)
        result = subprocess.run(cmd, shell = True)
        result.stdout
        
except:
        print('Error converting netCDF to geoTIFF')
        traceback.print_exc()

#Step 3: Convert each band of the GeoTIFF to its own raster



with rs.open(multiTIFF) as ds: # load parameter raster
        numBands = ds.count
        data = ds.read()
        profile = ds.profile
        paramNoData = ds.nodata
        tags = ds.tags()

print(profile)


day0 = datetime.datetime.strptime("01-01-1900", "%d-%m-%Y") #Set the day time is counted from


days = tags["NETCDF_DIM_day_VALUES"] #Get the list of dates associated with each band and convert to list
days = days.replace("{", "")
days = days.replace("}", "")
days = days.split(",")


#Create a list containing 12 empty lists
monthlyData = []
for month in range(1,13):
        monthlyData.append([])


i = 0 #Create counter for raster bands

for band in data:

        day = int(days[i]) #Get the days since beginning associated with the band
        
        
        date = day0 + datetime.timedelta(days=day) #Compute the date associated with the band
        print(date.strftime('%Y_%m_%d'))
        month = int(date.strftime("%m")) #Get month associated with band

        monthlyData[month-1].append(band) #Append the data to the appropriate month's list

        i = i + 1


#Update raster profile
profile.update({
        'dtype':'int16',
        'nodata':-1,
        'compress':'LZW',
        'profile':'GeoTIFF',
        'tiled':True,
        'count':1,
        'sparse_ok':True,
        'num_threads':'ALL_CPUS',
        'bigtiff':'IF_SAFER'})


for month in range(1,13):
        fileName = os.path.join(outDir, "{0}_{1}_{2}_00.tif".format(baseName, year, str(month).zfill(2))) #Create the name for the output file
        print(fileName)
        monthlyMin = np.mean(monthlyData[month-1], axis=0) #Compute average minimum temp in each cell for the month
        monthlyMin[monthlyMin == paramNoData] = -1
        monthlyMin = monthlyMin.astype(np.int16)
        
        with rs.open(fileName, 'w', **profile) as dst:
                dst.write(monthlyMin,1)

                print("Writing: " + fileName)
        



        


        i = i + 1
