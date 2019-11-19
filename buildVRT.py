import os
import subprocess
import traceback

#Requires gdal module (gdal/2.2.2-gcc) to be loaded

inDir = "../data/cov/landsatET"
outDir = "../data/cov/landsatET/vrt"
paramName = "landsat_ETmm"

rasterList = [] #Initialize list of covariates

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".tif":
                rasterList.append(os.path.join(path, name))




years = range(1985, 2019)


for year in years:

    yearRasters = [] #Create an empty list of rasters

    for raster in rasterList:
        if os.path.basename(raster).split("ET")[1].split("-")[0] == str(year):
             yearRasters.append(raster) #Add rasters from the current year to the list
    
    outFile = os.path.join(outDir, "{0}_{1}_00_00.vrt".format(paramName, year)) #Create output file path

    print(yearRasters)

    try:

        cmd = "gdalbuildvrt {0} {1}".format(outFile, " ".join(yearRasters)) # Create string of shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout

    except:
        print('Error Creating VRT')
        traceback.print_exc()
