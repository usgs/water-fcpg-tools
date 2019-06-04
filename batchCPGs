from tools import *



inDir = "../data/cov"
taufdr = "../data/tauDEM/taufdr1002"
taufac = "../data/tauDEM/taufac1002"
workDir = "../work/1002"
outDir = "../CPGs/1002"
HUC = "1002"

cores = 16

covList = [] #Initialize list of covariates

for path, subdirs, files in os.walk(inDir):
    for name in files:
        covList.append(os.path.join(path, name))



for cov in covList:

    #Create batch job which runs python script

