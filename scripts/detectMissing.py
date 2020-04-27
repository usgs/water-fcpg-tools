import os

HUClist = ["1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]

inDir = "../data/cov/static" # Source parameter grid folder.

CPGdir = "../FCPGs" # Output FCPG folder.

covList = [] #Initialize list of covariates

# iterate through all source parameter grids.
if os.path.isdir(inDir):

        for path, subdirs, files in os.walk(inDir):
                for name in files:
                        #Check if file is .tif, and if so add it to covariate list
                        if os.path.splitext(name)[1] == ".tif" or os.path.splitext(name)[1] == ".vrt":
                                covList.append(os.path.join(path, name))

        print("The following covariate files were located in the specified directory:")
        print(covList)

        missingList = [] #Initialize list of missing files

        # iterate through source grids and test if FCPGs have been created.
        for cov in covList:

                covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate

                if os.path.isdir(CPGdir):
                        for HUC in HUClist:
                                #Create the file name corresponding to the HUC and covariate
                                CPGFile = os.path.join(CPGdir, HUC,covname + "_HUC" + HUC +"_FCPG.tif") #Create filepath for parameter CPG file

                                if not os.path.isfile(CPGFile):
                                        print("Missing File: {0}".format(CPGFile))
                                        missingList.append(CPGFile)

                        
                else:
                        print("Error FCPG directory does  not exist: {0}".format(CPGdir))
                        
        print("{0} missing files found".format(len(missingList)))

else:
        print("Error input directory does  not exist: {0}".format(inDir))
