from tools import *

#Yeti Paths
fdr = "../100500010101/fdr100500010101.tif"
fac = "../100500010101/fac100500010101.tif"
taufdr = "../100500010101/work/taufdr100500010101.tif"


paramRast = "../100500010101/dem100500010101.tif"
accumParam = "../100500010101/work/demAccum100500010101.tif"

CPG = "../100500010101/work/elevCPG100500010101.tif"


tauDrainDir(fdr, taufdr)

accumulateParam(paramRast, taufdr, accumParam, cores = 1)


make_cpg(accumParam, fac, CPG)
