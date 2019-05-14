from tools import *

print(sys.argv)
print(type(sys.argv))

cores = 1 #Default number of cores to use

try:


    jobID = sys.argv[1] # pull the slurm job ID
    cores = int(sys.argv[2]) # pull the number of cores available

    print("jobID:%s"%jobID)
    print("Available Cores:%s"%cores)
except TypeError:
    print("Number of Cores set to 1")
    pass

#Inputs
fdr = "../1005/fdr1005.tif"
fac = "../1005/fac1005.tif"
paramRast = "../1005/dem1005.tif"

#Intermediate Ouputs
taufdr = "../1005/work/taufdr1005.tif"
accumParam = "../1005/work/demAccum1005.tif"

#CPG Output
CPG = "../1005/work/elevCPG1005.tif"


tauDrainDir(fdr, taufdr)

accumulateParam(paramRast, taufdr, accumParam, cores)


make_cpg(accumParam, fac, CPG)
