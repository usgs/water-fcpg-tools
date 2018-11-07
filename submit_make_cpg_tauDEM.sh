#!/bin/bash
#SBATCH --job-name=CPG # name that you chose
#SBATCH -c 1 # cpus per task
#SBATCH -n 32 # number of tasks
#SBATCH --tasks-per-node=16
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=16:00:00           # Overestimated guess at time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)  
#SBATCH --mem=128000            #memory in MB 

source activate py36
module load gis/TauDEM-5.3.8-gcc-mpich
module load gdal/2.2.2-gcc

python -u ./make_cpg_tauDEM.py $1 $SLURM_JOB_ID $SLURM_NTASKS
