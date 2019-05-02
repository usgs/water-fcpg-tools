from tools import *

#Yeti Paths
testFDR = "../100500010101/fdr100500010101.tif"
testOutput = "../100500010101/work/taufdr100500010101.tif"


tauDrainDir(testFDR, testOutput)

paramRast = "../100500010101/dem100500010101.tif"
outRast = "../100500010101/work/demAccum100500010101.tif"

accumulateParam(paramRast, testOutput, outRast, cores = 1)
