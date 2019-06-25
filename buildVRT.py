import os
import subprocess
import traceback

inDir = "../data/cov/landsatNDVI"
outDir = "../data/cov/landsatNDVI"

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
        if raster.split[4] == str(year):
             yearRasters.append(raster) #Add rasters from the current year to the list
    
    outFile = os.path.join(outDir, "landsat_NDVI-May-Oct_{0}_00_00.tif") #Create output file path


    try:

        cmd = 'gddalbuildvrt -d {0} {1}'.format(outFile, " ".join(yearRasters)) # Create string of tauDEM shell command
        print(cmd)
        #result = subprocess.run(cmd, shell = True) # Run shell command
        #result.stdout

        except:
        print('Error Accumulating Data')
        traceback.print_exc()
