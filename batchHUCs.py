import os
import subprocess
import traceback

HUClist = ["1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]


inDir = "../data/cov/SNODAS_SWEmm" 
taufdr = "../data/tauDEM" 
taufac = "../data/tauDEM" 
workDir = "../work"
outDir = "../CPGs"
logDir = "../logs"
cores = 20
accumThresh = 1000
overwrite = True
deleteTemp = True


for HUC in HUClist:

    HUCtaufdr = os.path.join(taufdr, "taufdr{0}.tif".format(HUC))
    HUCtaufac = os.path.join(taufac, "taufac{0}.tif".format(HUC))
    HUCworkDir = os.path.join(workDir, HUC)
    HUCoutDir = os.path.join(outDir, HUC)
    HUClogDir = os.path.join(logDir, HUC)

    try:
                
                cmd = 'python batchCPGs.py {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(inDir, HUCtaufdr, HUCtaufac, HUCworkDir, HUCoutDir, HUClogDir, cores, accumThresh, overwrite, deleteTemp) # Create string of shell command
                print(cmd)
                result = subprocess.run(cmd, shell = True) # Run shell command
                result.stdout
                
    except:
                print('Error sending command')
                traceback.print_exc()