#!/bin/bash
#SBATCH --job-name=get_NHDplus            
#SBATCH -c 1                                              
#SBATCH -p normal                                     
#SBATCH --account=wymtwsc                                    
#SBATCH --time=12:00:00                           
#SBATCH --mail-type=ALL                           
#SBATCH --mail-user=tbarnhart@usgs.gov    
#SBATCH -o %j.out          

cd /home/tbarnhart/projects/DEM_processing/data/NHDplusV21
wget -r --no-parent -l4 -A 'NHDPlusV21*Hydro?em*.7z' http://www.horizon-systems.com/NHDPlusData/NHDPlusV21/Data/ # grabs only some data

#wget -r --no-parent -A 'NHDPlusV21*HydroDem*.7z' http://www.horizon-systems.com/NHDPlusData/NHDPlusV21/Data/NHDPlus${reg}/
