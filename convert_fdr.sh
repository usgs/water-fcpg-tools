#!/bin/bash
# Script to move files and then run the aggregation script
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=convert_fdr # name that you chose
#SBATCH -n 1            # number of cores needed
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=12:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=20000 

cd ~/projects/CPGtools/data/NHDplusV21_facfdr/

for reg in {01..18}; do
	for fl in `ls -1 ./NHDPlusFdrFac${reg}*/fdr/hdr.adf`; do
		name=$(echo "$fl" | cut -f 2 -d '/')
		echo $fl
		echo ${name}_fdr.tif
		gdal_translate $fl ${name}_fdr.tif

	done
done
