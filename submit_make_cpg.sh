#!/bin/bash
# Script to move files and then run the aggregation script
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=mkCPG # name that you chose
#SBATCH -n 8            # number of cores needed
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=35:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=125000

# $1 region to process (int)
reg=$1 # region

echo Starting $reg CPG Creation

source activate py27 # load correct python environment
module load gis/grass-7.4-spack # load GRASS

grass74 ./grass/reg${reg}/PERMANENT --exec sh ./make_cpg.sh ${reg} # open grass and run the program

echo CPGs Created for $reg
