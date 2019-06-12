import os

inDir = "../CPGs/1003"
#inDir = "../data/cov/gridMET_PRmm" 

covList = [] # Initialize list

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".tif":
                covList.append(os.path.join(path, name))

for cov in covList:

    oldName = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate
    ext = os.path.splitext(os.path.basename(cov))[1] #Get the file extension

    nameParts = oldName.split("_")

    source = nameParts[0]
    var = nameParts[1]
    day = nameParts[2]
    month = nameParts[3]
    year = nameParts[4]
    HUC = nameParts[5]
    CPG = nameParts[6]
    
    newName = source + "_" + var + "_" + str(year) + "_" + str(month) + "_" + str(day) + "_" + HUC + "_" + CPG + ext
    
    #newName = source + "_" + var + "_" + str(year) + "_" + str(month) + "_" + str(day) + ext

    newPath = os.path.join(inDir, newName)

    print(cov)
    print(newPath)

    #os.rename(cov, newPath)