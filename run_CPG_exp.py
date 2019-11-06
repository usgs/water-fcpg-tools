import time
strt = time.time()
from tools import *
import sys
import geopandas as gpd

# make the CPG file first!

cov="./data/CHI_poster/daymet/daymet_v3_prcp_annttl_2017_na.tif"
taufdr="./data/CHI_poster/nhd/fdr_reclass.tif"
taufac="./data/CHI_poster/HRNHDPlusRasters1003/fac.tif"
workDir="./data/CHI_poster/cpg"
outDir="./data/CHI_poster/cpg"
cores=6
accumThresh=1000
overwrite=True
deleteTemp=False
HUC=str(1003)
outfl = "./data/CHI_poster/CPG_results.csv"

paramName = os.path.splitext(os.path.basename(cov))[0] 

#Prepare some file paths to things which will be created
rprjFile = os.path.join(workDir, paramName + "_HUC" + HUC + "rprj.tif") #Create filepath for reprojected parameter file
accumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accum.tif") #Create filepath for accumulated parameter file
nodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "nodata.tif") #Create filepath for parameter no data file
nodataaccumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accumnodata.tif") #Create filepath for parameter accumulated no data file
CPGFile = os.path.join(outDir, paramName + "_HUC" + HUC +"_CPG.tif") #Create filepath for parameter CPG file

resampleParam(cov, taufdr, rprjFile, resampleMethod="bilinear", cores=cores) #Resample and reprojected parameter raster
tauFlowAccum(taufdr,taufac,cores=cores)
accumulateParam(rprjFile, taufdr, accumFile, outNoDataRast=nodataFile, outNoDataAccum=nodataaccumFile, cores=cores) #Accumulate parameter
if os.path.isfile(nodataaccumFile):
    #If no data accumulation file was created, use it in call to create CPG
    make_cpg(accumFile, taufac, CPGFile, noDataRast=nodataaccumFile, minAccum=accumThresh) #Create parameter CPG
else:
    make_cpg(accumFile, taufac, CPGFile,  minAccum=accumThresh) #Create parameter CPG

totalTime = time.time() - strt

print("total time: %s seconds"%totalTime)
print("total time: %s minutes"%(totalTime/60.))