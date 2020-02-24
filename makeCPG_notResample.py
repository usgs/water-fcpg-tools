rom tools import *
import os
import datetime

"""
paramRast = os.path.abspath("../data/cov/gridMET_PRmm/gridMET_PRmm_31_12_2017.tif")
taufdr = os.path.abspath("../data/tauDEM/taufdr1002.tif") #Name must be in format taufdrXXXX.tif, where XXXX is a HUC code of any length
taufac = os.path.abspath("../data/tauDEM/taufac1002.tif")
workDir = os.path.abspath("../work/1002")
outDir = os.path.abspath("../CPGs/1002")
cores = 8
"""

def parsebool(b):
    return b == "True"

print("Starting {0}".format(datetime.datetime.now()))
#Set up Inputs
#print(sys.argv)
paramRast = sys.argv[1] #Path to parameter raster with name in format of "source_var_dd_mm_yyyy.tif"
taufdr = sys.argv[2] #Path to tauDEM flow direction grid with in format of "taufdrXXXX.tif", where XXXX is a HUC code of any length
taufac = sys.argv[3] #Path to tauDEM flow accumulation grid
workDir = sys.argv[4] #Path to working directory
outDir = sys.argv[5] #Path to output directory for CPG files
cores = int(sys.argv[6]) #Number of cores to use 
accumThresh = int(sys.argv[7]) #Number of cells in flow accumulation grid below which CPG will be set to no data
overwrite = parsebool(sys.argv[8]) #Whether to overwrite CPGs or not 
deleteTemp = parsebool(sys.argv[9]) #Whether to delete temporary files

print("Starting CPG process for:")
print("Parameter Raster: {0}".format(paramRast))
print("Flow Driection Grid: {0}".format(taufdr))
print("Flow Accumulation Grid: {0}".format(taufac))
print("Working Directory: {0}".format(workDir))
print("Output Directory: {0}".format(outDir))
print("Number of Cores: {0}".format(cores))
print("Accumulation Threshold: {0} cells".format(accumThresh))
print("Overwrite Existing CPG: {0}".format(overwrite))
print("Delete Temporary Files: {0}".format(deleteTemp))

#Get name of input parameter without extention
paramName = os.path.splitext(os.path.basename(paramRast))[0] 


#Get HUC number from tau flow direction raster name
try:
        HUC = os.path.splitext(os.path.basename(taufdr))[0].split("taufdr")[1]
except:
        print("Error - Flow direction raster has inappropriate name")

#Prepare some file paths to things which will be created
rprjFile = os.path.join(workDir, paramName + "_HUC" + HUC + "rprj.tif") #Create filepath for reprojected parameter file
accumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accum.tif") #Create filepath for accumulated parameter file
nodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "nodata.tif") #Create filepath for parameter no data file
nodataaccumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accumnodata.tif") #Create filepath for parameter accumulated no data file
zeronodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "zeronodata.tif") #Create filepath for parameter zeroed no data file
CPGFile = os.path.join(outDir, paramName + "_HUC" + HUC +"_CPG.tif") #Create filepath for parameter CPG file

if os.path.isfile(CPGFile) & (overwrite == False):
        print("Error: Specified CPG file exists and will not be overwritten")
else:
        #Run the CPG tools
        print("Calling resample function {0}".format(datetime.datetime.now()))
        #resampleParam(paramRast, taufdr, rprjFile, resampleMethod="bilinear", cores=cores) #Resample and reprojected parameter raster
        print("Calling flow accumulation function {0}".format(datetime.datetime.now()))
        accumulateParam(paramRast, taufdr, accumFile, outNoDataRast=nodataFile, outNoDataAccum=nodataaccumFile, zeroNoDataRast=zeronodataFile, cores=cores) #Accumulate parameter
        print("Calling make_cpg function {0}".format(datetime.datetime.now()))
        if os.path.isfile(nodataaccumFile):
                #If no data accumulation file was created, use it in call to create CPG
                make_cpg(accumFile, taufac, CPGFile, noDataRast=nodataaccumFile, minAccum=accumThresh) #Create parameter CPG
        else:
                make_cpg(accumFile, taufac, CPGFile,  minAccum=accumThresh) #Create parameter CPG
        
        if deleteTemp:
                try:
                        #Delete temporary files
                        os.remove(rprjFile)
                        os.remove(accumFile)
                        os.remove(nodataFile)
                        os.remove(nodataaccumFile)
                except:
                        print("Warning: Unable to delete temporary files")
print("Finished {0}".format(datetime.datetime.now()))