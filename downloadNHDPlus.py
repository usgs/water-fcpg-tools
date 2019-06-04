HUClist = ["1002"]

fileDir = "../data/NHDPlus"


for file in HUClist:
    downloadNHDPlusRaster(file, fileDir)