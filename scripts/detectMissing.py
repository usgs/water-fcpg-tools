import os

HUClist = ["1002", "1003", "1004"] # HUC4 geospatial tiles to search over.

inDir = "../data/cov/static" # Source parameter grid folder.

FCPGdir = "../FCPGs" # Output FCPG folder.

covList = [] #Initialize list of parameter grids.

# iterate through all source parameter grids.
if os.path.isdir(inDir):

        for path, subdirs, files in os.walk(inDir):
                for name in files:
                        #Check if file is .tif or .vrt file, and if so add it to covariate list
                        if os.path.splitext(name)[1] == ".tif" or os.path.splitext(name)[1] == ".vrt":
                                covList.append(os.path.join(path, name))

        print("The following covariate files were located in the specified directory:")
        print(covList)

        missingList = [] #Initialize list of missing files

        # iterate through source parameter grids and test if FCPGs have been created.
        for cov in covList:

                covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the parameter grid

                if os.path.isdir(FCPGdir):
                        for HUC in HUClist:
                                #Create the file name corresponding to the HUC and parameter grid
                                FCPGFile = os.path.join(FCPGdir, HUC,covname + "_HUC" + HUC +"_FCPG.tif") #Create filepath for parameter FCPG file

                                if not os.path.isfile(FCPGFile):
                                        print("Missing File: {0}".format(FCPGFile))
                                        missingList.append(FCPGFile)

                        
                else:
                        print("Error FCPG directory does  not exist: {0}".format(FCPGdir))
                        
        print("{0} missing files found".format(len(missingList)))

else:
        print("Error input directory does  not exist: {0}".format(inDir))
