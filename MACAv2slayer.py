import rasterio as rs
import numpy as np
import datetime
import os
import subprocess
import traceback

# Script to destroy the netCDF file Roy got from MACAv2
# Must have gdal and nco tools (module load tools/nco-4.7.8-gnu) modules loaded 

inDir = "../data/cov/macav2metdata" #Directory with netCDF files
#inDir = "../data/cov/macav2metdata/macav2metdata_pr_GFDL-ESM2G_r1i1p1_historical_1980_1984_CONUS_monthly.nc" #Directory with netCDF files
outDir = "../data/cov/MACAv2"
dataSource = "MACAv2" #Name of data source

#reorderCDF = "../data/cov/soil_gridMETfix.nc" #NetCDF file with reordered dimensions
#multiTIFF = "../data/cov/gridMET_SOILMOISTmm.tif" #Multiband .tif created from netCDF



covList = [] #Initialize list of covariates
if os.path.isdir(inDir):
    #Get all covariate files in directory
    for path, subdirs, files in os.walk(inDir):
        for name in files:
            #Check file type add it to covariate list
            if os.path.splitext(name)[1] == ".nc":
                    covList.append(os.path.join(path, name))
elif os.path.isfile(inDir):
    #Supplied path is a single covariate file
    covList.append(inDir)
else:
    print("Invalid covariate directory")



for cov in covList:
    
    baseName = os.path.basename(cov)
    param = baseName.split("_")[1] #Get the parameter name
    model = baseName.split("_")[2] #Get model used to generate the data
    scenario = baseName.split("_")[4] #Get the future scenario number (rcp4.5 of rcp8.5)
    startTime = baseName.split("_")[5] #Get the file start year
    endTime = baseName.split("_")[6] #Get the file start year

    reorderCDF = os.path.join(outDir, "{0}-{1}-{2}_{3}_{4}_{5}.nc".format(dataSource, model, scenario, param, startTime, endTime))

    multiTIFF = os.path.join(outDir, "{0}-{1}-{2}_{3}_{4}_{5}.nc".format(dataSource, model, scenario, param, startTime, endTime))


    print(baseName)
    print(reorderCDF)

    #Step 1: Put the file dimensions in the correct order

    try:
        cmd = "ncpdq -a time,lat,lon {0} {1}".format(cov, reorderCDF)
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


    days = tags["NETCDF_DIM_time_VALUES"] #Get the list of dates associated with each band and convert to list
    days = days.replace("{", "")
    days = days.replace("}", "")
    days = days.split(",")


    i = 0 

    for band in data:

        day = int(days[i]) #Get the days since beginning associated with the band
        
        date = day0 + datetime.timedelta(days=day) #Compute the date associated with the band

        fileName = os.path.join(outDir, dataSource + "-" +  model + "-" + scenario + "_" + param + "_" + date.strftime('%Y_%m_%d') + ".tif") #Create the name for the output file

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

