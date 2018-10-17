#!/bin/bash
# script to fill no data values with zero prior to CPG creation
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=mkCPG # name that you chose
#SBATCH -n 16            # number of cores needed
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=24:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=10000

for fl in `ls -1 ./data/cpg_datasets/*.tiff`; do
    filename=$(basename -- "$fl")
    varName="${filename%.*}"
    gdalwarp -co TILED=YES -co COMPRESS=LZW -co NUM_THREADS=ALL_CPUS -co SPARSE_OK=TRUE -co PROFILE=GeoTIFF -overwrite -dstnodata 0 $fl ./data/cpg_datasets/filled_data/${varName}_noDat.tiff
done
