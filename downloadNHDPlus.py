from tools import *

HUClist = ["1004"]

fileDir = "../data/NHDPlus"


for HUC in HUClist:
    downloadNHDPlusRaster(HUC, fileDir)