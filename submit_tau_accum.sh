#!/bin/bash
# Script to move files and then run the aggregation script
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=tauAccum # name that you chose
#SBATCH -c 1
#SBATCH -n 20
#SBATCH --tasks-per-node=20
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=24:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=128000
#SBATCH --exclusive


module load gis/TauDEM-5.3.8-gcc-mpich
module load gdal/2.2.2-gcc
source activate py36

cd ~/projects/CPGtools/data/NHDplusV21_facfdr/

for reg in {01..18}; do

inName=region_${reg}_fdr_tau.tif
outName=region_${reg}_fac_tau.tif
echo $inName
echo $outName
mpiexec -bind-to rr -n 20 aread8 -p $inName -ad8 $outName -nc

done
