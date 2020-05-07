import FCPGtools as fc
import os
import datetime
import sys

print("Starting {0}".format(datetime.datetime.now()))

# Set up Inputs
paramRast = sys.argv[1] # Path to parameter raster with name in format of "source_var_dd_mm_yyyy.tif"
taufdr = sys.argv[2] # Path to tauDEM flow direction grid with in format of "taufdrXXXX.tif", where XXXX is a HUC code of any length
taufac = sys.argv[3] # Path to tauDEM flow accumulation grid
workDir = sys.argv[4] # Path to working directory
outDir = sys.argv[5] # Path to output directory for FCPG files
cores = int(sys.argv[6]) # Number of cores to use 
accumThresh = int(sys.argv[7]) # Number of cells in flow accumulation grid below which FCPG will be set to no data
overwrite = fc.parsebool(sys.argv[8]) # Whether to overwrite CPGs or not 
deleteTemp = fc.parsebool(sys.argv[9]) # Whether to delete temporary files

print("Starting FCPG process for:")
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
rprjFile = os.path.join(workDir, paramName + "_HUC" + HUC + "rprj.tif") #Create filepath for reproject parameter file
accumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accum.tif") #Create filepath for accumulated parameter file
nodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "nodata.tif") #Create filepath for parameter no data file
nodataaccumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accumnodata.tif") #Create filepath for parameter accumulated no data file
zeronodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "zeronodata.tif") #Create filepath for parameter zeroed no data file
CPGFile = os.path.join(outDir, paramName + "_HUC" + HUC +"_FCPG.tif") #Create filepath for parameter FCPG file

if os.path.isfile(CPGFile) & (overwrite == False):
        print("Error: Specified FCPG file exists and will not be overwritten")
else:
        #Run the FCPG tools
        print("Calling resample function {0}".format(datetime.datetime.now()))
        fc.resampleParam(paramRast, taufdr, rprjFile, resampleMethod="bilinear", cores=cores) #Resample and reprojected parameter raster
        print("Calling flow accumulation function {0}".format(datetime.datetime.now()))
        fc.accumulateParam(rprjFile, taufdr, accumFile, outNoDataRast=nodataFile, outNoDataAccum=nodataaccumFile, zeroNoDataRast=zeronodataFile, cores=cores) #Accumulate parameter
        print("Calling make_cpg function {0}".format(datetime.datetime.now()))
        if os.path.isfile(nodataaccumFile):
                #If no data accumulation file was created, use it in call to create FCPG
                fc.make_cpg(accumFile, taufac, CPGFile, noDataRast=nodataaccumFile, minAccum=accumThresh) #Create parameter FCPG with no data raster.
        else:
                fc.make_cpg(accumFile, taufac, CPGFile,  minAccum=accumThresh) #Create parameter FCPG without no data raster.
        
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
