from tools import *

cores = 1
#Inputs
fdr = "../100500010101/fdr100500010101.tif"
fac = "../100500010101/fac100500010101.tif"
demRast = "../100500010101/dem100500010101.tif"
PRISMRast = "../100500010101/PRISM2015.tif"
inCat = "../100500010101/LandCoverMT.tif"









#Intermediate Ouputs
outWorkspace = "../100500010101/work"
taufdr = "../100500010101/work/taufdr100500010101.tif"

rprjPRISM = "../100500010101/work/PRISMrprj100500010101.tif"
rprj149 = "../100500010101/work/149rprj100500010101.tif"

accumDEM = "../100500010101/work/demAccum100500010101.tif"
accumPRISM = "../100500010101/work/PRISMAccum100500010101.tif"
accum149 = "../100500010101/work/149Accum100500010101.tif"

#CPG Output
elevCPG = "../100500010101/work/elevCPG100500010101.tif"
PRISMCPG = "../100500010101/work/PRISMCPG100500010101.tif"
CPG149 = "../100500010101/work/149CPG100500010101.tif"


print("Creating Binary Parameter Grids...")
binaryList = cat2bin(inCat, outWorkspace)

print("Creating tauDEM Drainage Directions...")
tauDrainDir(fdr, taufdr)

print("Resampling Rasters...")
#resampleParam(PRISMRast, fdr, rprjPRISM, resampleMethod="bilinear", cores=cores)
#resampleParam("../100500010101/work/LandCoverMT149.tif", fdr, rprj149, resampleMethod="near", cores=cores)
resampledList = resampleParams(binaryList, taufdr, outWorkspace, resampleMethod="bilinear", cores=cores, appStr="rprj")

print("Accumulating Parameters...")
#accumulateParam(demRast, taufdr, accumDEM, cores)
#accumulateParam(rprjPRISM, taufdr, accumPRISM, cores)
#accumulateParam(rprj149, taufdr, accum149, cores)

accumulatedList = accumulateParams(resampledList, taufdr, outWorkspace, cores=cores, appStr="accum")



print("Creating CPGs...")
#make_cpg(accumDEM, fac, elevCPG)
#make_cpg(accumPRISM, fac, PRISMCPG)
#make_cpg(accum149, fac, CPG149)

CPGList = make_cpgs(accumulatedList, fac, outWorkspace, appStr="CPG")
