from tools import *

#Inputs
fdr = "../100500010101/fdr100500010101.tif"
fac = "../100500010101/fac100500010101.tif"
demRast = "../100500010101/dem100500010101.tif"
PRISMRast = "../100500010101/PRISM2015.tif"
inCat = "../100500010101/LandCoverMT.tif"



cat2bin(inCat, outWorkspace)





#Intermediate Ouputs
outWorkspace = "../100500010101/work"
taufdr = "../100500010101/work/taufdr100500010101.tif"

rprjPRISM = "../100500010101/work/PRISMrprj100500010101.tif"
rprj270 = "../100500010101/work/270rprj100500010101.tif"

accumDEM = "../100500010101/work/demAccum100500010101.tif"
accumPRISM = "../100500010101/work/PRISMAccum100500010101.tif"


#CPG Output
elevCPG = "../100500010101/work/elevCPG100500010101.tif"
PRISMCPG = "../100500010101/work/PRISMCPG100500010101.tif"

print("Create tauDEM Drainage Directions...")
tauDrainDir(fdr, taufdr)

print("Resampling Rasters...")
resampleParam(PRISMRast, fdr, rprjPRISM, resampleMethod="bilinear", cores=cores)
resampleParam("../100500010101/work/LandCoverMT270.tif", fdr, rprj270, resampleMethod="nearest", cores=cores)

print("Accumulating Parameters...")
accumulateParam(demRast, taufdr, accumDEM, cores)
accumulateParam(rprjPRISM, taufdr, accumPRISM, cores)


print("Creating CPGs...")
make_cpg(accumDEM, fac, elevCPG)
make_cpg(accumPRISM, fac, PRISMCPG)