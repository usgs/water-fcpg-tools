from tools import *

HUClist = ["1003"]

fileDir = "../data/NHDPlus"


for HUC in HUClist:
    downloadNHDPlusRaster(HUC, fileDir)