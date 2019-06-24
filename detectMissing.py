import os

HUClist = []

CPGdir = "../CPGs"

covList = [] #Initialize list of covariates

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".tif":
                covList.append(os.path.join(path, name))

print("The following covariate files were located in the specified directory:")
print(covList)

missingList = [] #Initialize list of missing files

for cov in covList:

    covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate

    for HUC in HUClist:
        #Create the fiel name corresponding to the HUC and covariate
        CPGFile = os.path.join(CPGdir, covname + "_HUC" + HUC +"_CPG.tif") #Create filepath for parameter CPG file

        if not os.path.isfile(CPGFile):
            print("Missing File: {0}".format(CPGFile))
