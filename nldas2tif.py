import rasterio as rs
import numpy as np
import datetime
import os
import subprocess
import traceback

# Script to destroy the netCDF file Roy got from gridMET
# Must have gdal and nco tools (module load tools/nco-4.7.8-gnu) modules loaded 

inDir = "../data/cov/nldas"

inCDF = "../data/cov/nldas/NLDAS_VIC0125_M.A197901.002.grb.SUB.nc4 " #Original netCDF from gridMET_SOILMOISTmm
reorderCDF = "../data/cov/nldas/nldas_SOILMOISTkgm2_1979_01.nc" #NetCDF file with reordered dimensions
multiTIFF = "../data/cov/nldas/nldas_SOILMOISTkgm2_1979_01.tif" #Multiband .tif created from netCDF

year = "1979"

month = "01"

baseName = "nldas_SOILMOISTkgm2"

outDir = "../data/cov/nldas_SOILMOISTkgm2"

#Step 1: Put the file dimensions in the correct order

try:
        cmd = "ncpdq -a time,lev,lat,lon {0} {1}".format(inCDF, reorderCDF)
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

#Step 3: Extract the band(s) we want from the GeoTIFF to individual rasters

with rs.open(multiTIFF) as ds: # load parameter raster
        numBands = ds.count
        data = ds.read()
        profile = ds.profile
        paramNoData = ds.nodata
        tags = ds.tags()

print(profile)

band = data[3] #Get 3rd band (total column soil moisture)

fileName = os.path.join(outDir, baseName + "_" + year + "_" + month + ".tif") #Create the name for the output file

#Update raster profile
profile.update({
        'compress':'LZW',
        'profile':'GeoTIFF',
        'tiled':True,
        'count':1,
        'sparse_ok':True,
        'num_threads':'ALL_CPUS',
        'bigtiff':'IF_SAFER'})

with rs.open(fileName, 'w', **profile) as dst:
        dst.write(band,1)

        print("Writing: " + fileName)

#day0 = datetime.datetime.strptime("01-01-1900", "%d-%m-%Y") #Set the day time is counted from


#days = tags["NETCDF_DIM_time_VALUES"] #Get the list of dates associated with each band and convert to list
#days = days.replace("{", "")
#days = days.replace("}", "")
#days = days.split(",")

"""
i = 0 

for band in data:

        day = int(days[i]) #Get the days since beginning associated with the band
        
        date = day0 + datetime.timedelta(days=day) #Compute the date associated with the band

        fileName = os.path.join(outDir, baseName + "_" + date.strftime('%Y_%m_%d') + ".tif") #Create the name for the output file

        #Update raster profile
        profile.update({
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'count':1,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'bigtiff':'IF_SAFER'})

        with rs.open(fileName, 'w', **profile) as dst:
                dst.write(band,1)

                print("Writing: " + fileName)




        


        i = i + 1


"""

