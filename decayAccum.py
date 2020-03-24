import os
import numpy as np
import rasterio as rs
import datetime
import subprocess
import traceback
from tools import *




#makeDecayGrid("../data/tauDEM/tauDist2Strm1002.tif", "../data/tauDEM/invDist1002.tif")

#resampleParam("../data/cov/landsatNDVI/vrt/landsat_NDVI-May-Oct_2018_00_00.vrt", "../data/tauDEM/taufdr1002.tif", "../work/1002/landsat_NDVI-May-Oct_2018_00_00rprj.tif", resampleMethod="bilinear", cores=20)

#decayAccum("../data/tauDEM/tauDINFang1002.tif",  "../data/tauDEM/invDist1002.tif", "../work/1002/paramdecayAccumTest.tif", paramRast="../work/1002/landsat_NDVI-May-Oct_2018_00_00rprj.tif", cores=20)

#decayAccum("../data/tauDEM/tauDINFang1002.tif", "../data/tauDEM/invDist1002.tif", "../work/1002/decayAccumTest.tif", cores=20)

#make_Decaycpg("../work/1002/paramdecayAccumTest.tif", "../work/1002/decayAccumTest.tif", "../work/1002/decayAccumCPGTest.tif", streamMask ="../CPGs/1002/gridMET_minTempK_1979_01_00_HUC1002_CPG.tif")


HUCs = ["1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]

for HUC in HUCs:
    #dist2stream("../data/tauDEM/taufdr{0}.tif".format(HUC), "../data/tauDEM/taufac{0}.tif".format(HUC), 1000, "../data/tauDEM/tauDist2Strm{0}.tif".format(HUC), cores=20)
    #makeDecayGrid("../data/tauDEM/tauDist2Strm{0}.tif".format(HUC), "../data/tauDEM/invDecay{0}.tif".format(HUC))
    accumulateParam("../data/tauDEM/invDecay{0}.tif".format(HUC), "../data/tauDEM/taufdr{0}.tif".format(HUC), "../data/tauDEM/decayfac{0}.tif".format(HUC), outNoDataRast = None, outNoDataAccum = None, cores = 20)