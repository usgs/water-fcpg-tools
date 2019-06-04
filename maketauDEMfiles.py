from tools import *

#HUClist = ["1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012"]

HUClist = ["1003", "1004"]
outDir = "../data/tauDEM"

cores = 16

for HUC in HUClist:

    fdr = "../data/NHDPlus/HRNHDPlusRasters{0}/fdr.tif".format(HUC)
    taufdr = os.path.join(outDir, "taufdr" + HUC + ".tif")
    taufac = os.path.join(outDir, "taufac" + HUC + ".tif")
    
    tauDrainDir(fdr, taufdr)
    tauFlowAccum(taufdr, taufac, cores=cores)


