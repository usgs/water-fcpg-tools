from tools import *

if sys.argv[0] != None:
    inDir = sys.argv[0] #Input directory in which to search for parameter rasters
    taufdr = sys.argv[1] #Flow direction grid in tauDEM format
    taufac = sys.argv[2] #Flow accumulation grid in tauDEM format
    workDir = sys.argv[3] #Working directory to save intermediate files
    outDir = sys.argv[4] #Output directory to save CPGs
    cores = sys.argv[5] #Number of cores to use for each slurm job

else:
    #If inputs aren't specified in system args, set them in the script
    inDir = "../data/tauDEM" 
    taufdr = "../data/tauDEM/taufdr1002.tif" 
    taufac = "../data/tauDEM/taufac1002.tif" 
    workDir = "../work"
    outDir = "../CPGs/1002"
    cores = 16

covList = [] #Initialize list of covariates

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".tif":
                covList.append(os.path.join(path, name))

print("The following covariate files were located in the specified directory:")
print(covList)


for cov in covList:

    covname = os.path.splitext(os.path.basename(cov))[0] #Get the name of the covariate

    #Create batch job which runs python script
    
    jobfile = os.path.join(workDir, "{0}.slurm".format(str(covname))) # Create path to slurm job file, consider adding timestamp in name?

    with open(jobfile, 'w+') as f:
        
        #Write slurm job details
        f.writelines("#!/bin/bash\n")
        f.writelines("#SBATCH --job-name=%s.job\n" %covname)
        f.writelines("#SBATCH -c 1\n") # cpus per task
        f.writelines("#SBATCH -n {0}\n".format(cores)) # number of tasks
        #f.writelines("#SBATCH --tasks-per-node=8\n") # Set number of tasks per node
        f.writelines("#SBATCH -p normal\n") # the partition you want to use, for this case prod is best
        f.writelines("#SBATCH --account=wymtwsc\n") # your account
        f.writelines("#SBATCH --time=00:10:00\n") # Overestimated guess at time
        f.writelines("#SBATCH --mem=128000\n") #memory in MB
        f.writelines("#SBATCH --mail-type=ALL\n") # Send email on all events
        f.writelines("#SBATCH --mail-user=$USER@usgs.gov\n")

        #Set up python environment for job
        f.writelines("module load gis/TauDEM-5.3.8-gcc-mpich\n")
        f.writelines("module load gdal/2.2.2-gcc\n")
        f.writelines("source activate py36\n")

        #Run the python script
        f.writelines("python -u ./makeCPG.py {0} {1} {2} {3} {4} {5}\n".format(cov, taufdr, taufac, workDir, outDir, cores))

    #os.system("sbatch {0}".format(jobfile)) #Send command to console

