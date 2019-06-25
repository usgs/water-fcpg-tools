import os
import subprocess
import traceback



rasterList = [] #Initialize list of covariates

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".tif":
                rasterList.append(os.path.join(path, name))




years = range(1985, 2019)


for year in years:

    rasterList = [] #Create an empty list of rasters

    for raster in rasterList:
            if raster.split[4] == str(year):
                    rasterList.append(raster) #Add rasters from the current year to the list

    try:

        cmd = 'gddalbuildvrt -bind-to rr -n {cores} aread8 -p {fdr} -ad8 {outFl} -wg {weight} -nc'.format(**tauParams) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        result.stdout
        print("Parameter no data accumulation written to: {0}".format(outNoDataRast))

        except:
        print('Error Accumulating Data')
        traceback.print_exc()
