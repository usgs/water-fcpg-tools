#!/bin/bash
# Script to move files and then run the aggregation script
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=snap # name that you chose
#SBATCH -n 1            # number of cores needed
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=04:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=120000

source activate py27
module load gis/grass-7.4-spack

grass74 ./grass/reg${1}/PERMANENT --exec sh snap_gauges.sh $1 $2
