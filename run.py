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
fdr = "../10f/fdr10f.tif"
fac = "../10f/fac10f.tif"
demRast = "../10f/dem10f.tif"
PRISMRast = "../10f/PRISM2015.tif"

#Intermediate Ouputs
taufdr = "../10f/work/taufdr10f.tif"
accumDEM = "../10f/work/demAccum10f.tif"

rprjPRISM = "../10f/work/PRISMrprj10f.tif"
accumPRISM = "../10f/work/PRISMAccum10f.tif"


#CPG Output
elevCPG = "../10f/work/elevCPG10f.tif"
PRISMCPG = "../10f/work/PRISMCPG10f.tif"

print("Create tauDEM Drainage Directions...")
tauDrainDir(fdr, taufdr)

print("Resampling Rasters...")
resampleParam(PRISMRast, fdr, rprjPRISM, resampleMethod="bilinear", cores=1)

print("Accumulating Parameters...")
accumulateParam(demRast, taufdr, accumDEM, cores)
accumulateParam(PRISMRast, taufdr, accumPRISM, cores)

print("Creating CPGs...")
make_cpg(accumDEM, fac, elevCPG)
make_cpg(accumPRISM, fac, PRISMCPG)
