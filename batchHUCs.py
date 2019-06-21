import os

HUClist = []


inDir = "../data/cov/gridMET_SOILMOISTmm" 
taufdr = "../data/tauDEM" 
taufac = "../data/tauDEM" 
workDir = "../work"
outDir = "../CPGs"
logDir = "../logs"
cores = 20
accumThresh = 1000
overwrite = True


for HUC in HUClist:

    HUCtaufdr = os.path.join(taufdr, "taufdr{0}.tif".format(HUC))
    HUCtaufac = os.path.join(taufac, "taufac{0}.tif".format(HUC))
    HUCworkDir = os.path.join(workDir, HUC)
    HUCoutDir = os.path.join(outDir, HUC)
    HUClogDir = os.path.join(logDir, HUC)