from tools import *

HUCs = ["1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]


for HUC in HUCs:

    streamDist = "../data/tauDEM/tauDist2Strm{0}.tif".format(HUC)
    decayRast = "../data/tauDEM/oneFourthDecay{0}.tif".format(HUC)

    makeDecayGrid(streamDist, 4, decayRast) #Create decay grid with multiplier of 4
