from tools import *

#Inputs
fdr = "../100500010101b/fdr100500010101b.tif"
fac = "../100500010101b/fac100500010101b.tif"
paramRast = "../100500010101b/dem100500010101b.tif"

#Intermediate Ouputs
taufdr = "../100500010101b/work/taufdr100500010101b.tif"
accumParam = "../100500010101b/work/demAccum100500010101b.tif"

#CPG Output
CPG = "../100500010101b/work/elevCPG100500010101b.tif"


tauDrainDir(fdr, taufdr)

accumulateParam(paramRast, taufdr, accumParam, cores = 10)


make_cpg(accumParam, fac, CPG)
