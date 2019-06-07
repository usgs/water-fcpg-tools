from tools import *
import os


paramRast = os.path.abspath("../data/cov/gridMET_PRmm/gridMET_PRmm_31_12_2017.tif")
taufdr = os.path.abspath("../data/tauDEM/taufdr1002.tif") #Name must be in format taufdrXXXX.tif, where XXXX is a HUC code of any length
taufac = os.path.abspath("../data/tauDEM/taufac1002.tif")
workDir = os.path.abspath("../work/1002")
outDir = os.path.abspath("../CPGs/1002")
cores = 16
"""

#Set up Inputs
paramRast = sys.argv[0] #Path to parameter raster with name in format of "source_var_dd_mm_yyyy.tif"
taufdr = sys.argv[1] #Path to tauDEM flow direction grid with in format of "taufdrXXXX.tif", where XXXX is a HUC code of any length
taufac = sys.argv[2] #Path to tauDEM flow accumulation grid
workDir = sys.argv[3] #Path to working directory
outDir = sys.argv[4] #Path to output directory for CPG files
cores = int(sys.argv[5]) #Number of cores to use 
"""
print(paramRast)
print(taufdr)
print(taufac)
print(workDir)
print(outDir)
print(cores)

#Get name of input parameter without extention
paramName = os.path.splitext(os.path.basename(paramRast))[0] 

#Get HUC number from tau flow direction raster name
try:
        HUC = os.path.splitext(os.path.basename(taufdr))[0].split("taufdr")[0]
except:
        print("Error - Flow direction raster has inappropriate name")

#Prepare some file paths to things which will be created
rprjFile = os.path.join(workDir, paramName + "rprj.tif") #Create filepath for reprojected parameter file
accumFile = os.path.join(workDir, paramName + "accum.tif") #Create filepath for accumulated parameter file
nodataFile = os.path.join(workDir, paramName + "nodata.tif") #Create filepath for parameter no data file
nodataaccumFile = os.path.join(workDir, paramName + "accumnodata.tif") #Create filepath for parameter accumulated no data file
CPGFile = os.path.join(outDir, paramName + "_HUC" + HUC +"_CPG.tif") #Create filepath for parameter CPG file

#Run the CPG tools

resampleParam(paramRast, taufdr, rprjFile, resampleMethod="bilinear", cores=cores) #Resample and reprojected parameter raster
accumulateParam(rprjFile, taufdr, accumFile, outNoDataRast=nodataFile, outNoDataAccum=nodataaccumFile, cores=cores) #Accumulate parameter

if os.path.isfile(nodataaccumFile):
        #If no data accumulation file was created, use it in call to create CPG
        make_cpg(accumFile, taufac, CPGFile, noDataRast=nodataaccumFile, minAccum=100) #Create parameter CPG
else:
        make_cpg(accumFile, taufac, CPGFile,  minAccum=100) #Create parameter CPG