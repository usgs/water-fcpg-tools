from tools import *

HUClist = ["1002"]

fileDir = "../data/NHDPlus"


for HUC in HUClist:
    downloadNHDPlusRaster(HUC, fileDir)