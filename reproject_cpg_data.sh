#!/bin/bash
# Script to move files and then run the aggregation script
# Theodore Barnhart | tbarnhart@usgs.gov

#SBATCH --job-name=reproject # name that you chose
#SBATCH -n 1            # number of cores needed
#SBATCH -p normal                         # the partition you want to use, for this case prod is best
#SBATCH --account=wymtwsc        # your account
#SBATCH --time=3:00:00           # Overestimated time
#SBATCH --mail-type=ALL         # Send email on all events
#SBATCH --mail-user=tbarnhart@usgs.gov
#SBATCH  -o %j.log                    # Sets output log file to %j ( will be the jobId returned by sbatch)
#SBATCH --mem=20000

# $1 - resampling method
# $2 - infile
# $3 - outfile

source activate py36

ssrs="EPSG:42303"
#ssrs='PROJCS["Sphere_ARC_INFO_Lambert_Azimuthal_Equal_Area",GEOGCS["GCS_Sphere_ARC_INFO",DATUM["D_Sphere_ARC_INFO",SPHEROID["Sphere_ARC_INFO",6370997.0,0.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-100.0],PARAMETER["Latitude_Of_Origin",45.0],UNIT["Meter",1.0]]'

gdalwarp -overwrite -tr 30 30 -t_srs EPSG:42303 -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -s_srs $ssrs -r $1 $2 $3


ssrs="+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,-0,-0,-0,0 +units=m +no_defs"
gdalwarp -overwrite -tr 30 30 -t_srs EPSG:42303 -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -s_srs $ssrs