from tools import *
import time

#Check if system arguments were provided
if len(sys.argv) > 1:
    inDir = sys.argv[1] #Input directory in which to search for parameter rasters
    taufdr = sys.argv[2] #Flow direction grid in tauDEM format
    taufac = sys.argv[3] #Flow accumulation grid in tauDEM format
    workDir = sys.argv[4] #Working directory to save intermediate files
    outDir = sys.argv[5] #Output directory to save CPGs
    logDir = sys.argv[6] #Directory to save slurm log files
    cores = sys.argv[7] #Number of cores to use for each slurm job
    accumThresh = sys.argv[8] #Number of cells in flow accumulation grid below which CPG will be set to no data
    overwrite = sys.argv[9] #Whether to overwrite existing CPGs
    deleteTemp = sys.argv[10] #Whether to delete temporary files
else:
    #If inputs aren't specified in system args, set them in the script
    inDir = "../data/cov/SNODAS_SWEmm/SNODAS_SWEmm_2006_03_01.tif" 
    taufdr = "../data/tauDEM/taufdr1012.tif" 
    taufac = "../data/tauDEM/taufac1012.tif" 
    workDir = "../work/1012"
    outDir = "../CPGs/1012"
    logDir = "../logs/1012"
    cores = 20
    accumThresh = 1000
    overwrite = True
    deleteTemp = True

covList = [] #Initialize list of covariates

if os.path.isdir(inDir):
    #Get all covariate files in directory
    for path, subdirs, files in os.walk(inDir):
        for name in files:
            #Check if file is .tif, and if so add it to covariate list
            if os.path.splitext(name)[1] == ".tif":
                    covList.append(os.path.join(path, name))
elif os.path.isfile(inDir):
    #Supplied path is a single covariate file
    covList.append(inDir)
else:
    print("Invalid covariate directory")

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
        f.writelines("#SBATCH --tasks-per-node=20\n") # Set number of tasks per node
        f.writelines("#SBATCH -o {0}/slurm-%A.out\n".format(logDir)) # Set log file name 
        f.writelines("#SBATCH -p normal\n") # the partition you want to use, for this case prod is best
        f.writelines("#SBATCH --account=wymtwsc\n") # your account
        f.writelines("#SBATCH --time=01:00:00\n") # Overestimated guess at time
        f.writelines("#SBATCH --mem=128000\n") #memory in MB
        f.writelines("#SBATCH --mail-type=ALL\n") # Send email only for all events
        f.writelines("#SBATCH --mail-user={0}@usgs.gov\n".format(os.getlogin()))
        f.writelines("#SBATCH --exclusive\n") # Require exclusive use of nodes

        #Set up python environment for job
        f.writelines("module load gis/TauDEM-5.3.8-gcc-mpich\n")
        f.writelines("module load gdal/2.2.2-gcc\n")
        f.writelines("source activate py36\n")

        #Run the python script
        f.writelines("python -u ./makeCPG.py {0} {1} {2} {3} {4} {5} {6} {7} {8}\n".format(cov, taufdr, taufac, workDir, outDir, cores, accumThresh, overwrite, deleteTemp))
        
    print("Launching batch job for: " + str(covname))

    os.system("sbatch {0}".format(jobfile)) #Send command to console

    time.sleep(5) #Wait between submitting jobs
