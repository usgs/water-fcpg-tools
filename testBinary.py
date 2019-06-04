from tools import *

cores = 32
#Inputs
fdr = "../1005/fdr1005.tif"
#fac = "../1005/fac1005.tif"
demRast = "../1005/dem1005.tif"
PRISMRast = "../1005/PRISM2015.tif"
inCat = "../1005/LandCoverMT.tif"









#Intermediate Ouputs
outWorkspace = "../1005/work"
taufdr = "../1005/work/taufdr1005.tif"
taufac = "../1005/work/taufac1005.tif"

rprjPRISM = "../1005/work/PRISMrprj1005.tif"
rprj149 = "../1005/work/149rprj1005.tif"

accumDEM = "../1005/work/demAccum1005.tif"
accumPRISM = "../1005/work/PRISMAccum1005.tif"
accum149 = "../1005/work/149Accum1005.tif"

PRISMnodata = "../1005/work/PRISMnodata1005.tif"
PRISMnodataaccum = "../1005/work/PRISMnodataaccum1005.tif"

#CPG Output
elevCPG = "../1005/work/elevCPG1005.tif"
PRISMCPG = "../1005/work/PRISMCPG1005.tif"
CPG149 = "../1005/work/149CPG1005.tif"


print("Creating Binary Parameter Grids...")
#binaryList = cat2bin(inCat, outWorkspace)
#binaryList = ["../100500010101/work/LandCoverMT311.tif"]

print("Creating tauDEM Drainage Directions...")
#tauDrainDir(fdr, taufdr)
#tauFlowAccum(taufdr, taufac, cores=cores)



print("Resampling Rasters...")
#resampleParam(PRISMRast, fdr, rprjPRISM, resampleMethod="bilinear", cores=cores)
#resampledList = resampleParams(binaryList, taufdr, outWorkspace, resampleMethod="near", cores=cores, appStr="rprj")

print("Accumulating Parameters...")
#accumulateParam(demRast, taufdr, accumDEM, cores=cores)
#accumulateParam(rprjPRISM, taufdr, accumPRISM, outNoDataRast=PRISMnodata, outNoDataAccum=PRISMnodataaccum, cores=cores)

#accumulatedList = accumulateParams(resampledList, taufdr, outWorkspace, cores=cores, appStr="accum")



print("Creating CPGs...")
#make_cpg(accumDEM, taufac, elevCPG, minAccum=100)
make_cpg(accumPRISM, taufac, PRISMCPG, noDataRast=PRISMnodata, minAccum=100)

#CPGList = make_cpgs(accumulatedList, taufac, outWorkspace, minAccum=100, appStr="CPG")
