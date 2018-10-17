#!/bin/bash
#SBATCH --job-name=get_NHDplus            
#SBATCH -c 1                                              
#SBATCH -p normal                                     
#SBATCH --account=wymtwsc                                    
#SBATCH --time=12:00:00                           
#SBATCH --mail-type=ALL                           
#SBATCH --mail-user=tbarnhart@usgs.gov    
#SBATCH -o %j.out

source activate py36 # load python environment

python reclassify_drain_dir.py $1 # pass command line argument of region to process