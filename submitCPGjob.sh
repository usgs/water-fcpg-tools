#!/bin/bash
#SBATCH --job-name=CPG # name that you chose
#SBATCH -c 1 # cpus per task
#SBATCH -n 8 # number of tasks
#SBATCH --tasks-per-node=8
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=1:00:00           # Overestimated guess at time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=ssiefken@usgs.gov
#SBATCH -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)  
#SBATCH --mem=128000            #memory in MB 


module load gis/TauDEM-5.3.8-gcc-mpich
module load gdal/2.2.2-gcc
source activate py36


python -u ./makeCPG.py $SLURM_JOB_ID $SLURM_NTASKS

echo $SLURM_NTASKS
