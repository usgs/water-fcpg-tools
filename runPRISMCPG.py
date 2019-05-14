from tools import *

print(sys.argv)

cores = 1 #Default number of cores to use

try:
    if len(sys.argv == 3):

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
#paramRast = "../1005/dem1005.tif"
paramRast = "../1005/2015PRISM_Milk.tif"

#Intermediate Ouputs
taufdr = "../1005/work/taufdr1005.tif"
rprjParam = "../1005/work/PRISMrprj1005.tif"
accumParam = "../1005/work/PRISMAccum1005.tif"

#CPG Output
CPG = "../1005/work/PRISMCPG1005.tif"

print("Create tauDEM Drainage Directions...")
tauDrainDir(fdr, taufdr)

print("Resampling Parameter Raster...")
resampleParam(paramRast, fdr, rprjParam, resampleMethod="bilinear", threads=2)

print("Accumulating Parameter...")
accumulateParam(rprjParam, taufdr, accumParam, cores)


make_cpg(accumParam, fac, CPG)

