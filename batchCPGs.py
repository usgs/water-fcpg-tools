from tools import *



inDir = "../data/tauDEM"
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

print(covList)

"""
for cov in covList:

    covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate

    #Create batch job which runs python script
    
    jobfile = os.path.join(workDir, "{0}.slurm".format(str(covname))) # Create path to slurm job file, consider adding timestamp in name?

    with open(jobfile) as f:
        
        #Write slurm job details
        f.writelines("#!/bin/bash")
        f.writelines("#SBATCH --job-name=%s.job\n" %covname)
        f.writelines("#SBATCH -c 1\n") # cpus per task
        f.writelines("#SBATCH -n {0}\n".format(cores)) # number of tasks
        f.writelines("#SBATCH --tasks-per-node=8\n" %covname) # Set number of tasks per node
        f.writelines("#SBATCH -p normal\n") # the partition you want to use, for this case prod is best
        f.writelines("#SBATCH --account=wymtwsc") # your account
        f.writelines("#SBATCH --time=04:00:00\n") # Overestimated guess at time
        f.writelines("#SBATCH --mem=128000\n") #memory in MB
        f.writelines("#SBATCH --mail-type=ALL\n") # Send email on all events
        f.writelines("#SBATCH --mail-user=$USER@usgs.gov\n")

        #Set up python environment for job
        f.writelines("module load gis/TauDEM-5.3.8-gcc-mpich\n")
        f.writelines("module load gdal/2.2.2-gcc\n")
        f.writelines("source activate py36\n")

        #Run the python script
        f.writelines("python -u ./makeCPG.py {0} {1} \n".format(arg1, arg2, ...))
"""
    #os.system("sbatch %s" %jobfile) #Send command to console

