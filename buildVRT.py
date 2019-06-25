import os
import subprocess
import traceback

inDir = "../data/cov/landsatNDVI"
outDir = "../data/cov/landsatNDVI/vrt"

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
        if os.path.basename(raster).split("_")[4].split("-")[0] == str(year):
             yearRasters.append(raster) #Add rasters from the current year to the list
    
    outFile = os.path.join(outDir, "landsat_NDVI-May-Oct_{0}_00_00.vrt".format(year)) #Create output file path

    print(yearRasters)

    try:

        cmd = "gddalbuildvrt -d {0} {1}".format(outFile, " ".join(yearRasters)) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout

    except:
        print('Error Accumulating Data')
        traceback.print_exc()
