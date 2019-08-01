from tools import *
streamDist = "../data/tauDEM/tauDist2Strm1002.tif"
decayRast = "../data/tauDEM/oneFourthDecay1002.tif"
makeDecayGrid(streamDist, 4, decayRast)
