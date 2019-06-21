import os

HUClist = []

    inDir = "../data/cov/gridMET_SOILMOISTmm" 
    taufdr = "../data/tauDEM" 
    taufac = "../data/tauDEM" 
    workDir = "../work/"
    outDir = "../CPGs/"
    logDir = "../logs/"
    cores = 20
    accumThresh = 1000
    overwrite = True

for HUC in HUClist:

    fdr = "../data/NHDPlus05_06_2019/HRNHDPlusRasters{0}/fdr.tif".format(HUC)
    taufdr = os.path.join(outDir, "taufdr" + HUC + ".tif")
    taufac = os.path.join(outDir, "taufac" + HUC + ".tif")
    
    tauDrainDir(fdr, taufdr)
    #tauFlowAccum(taufdr, taufac, cores=cores)

