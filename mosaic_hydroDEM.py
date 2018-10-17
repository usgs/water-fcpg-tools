# load the 

import glob
import subprocess

regions = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18']

for reg in regions:

    cmd = "gdalbuildvrt /home/tbarnhart/projects/DEM_processing/data/NHDplusV21/region_%s.vrt /home/tbarnhart/projects/DEM_processing/data/NHDplusV21/NHDPlusHydrodem%s*/hydrodem/hdr.adf"%(reg,reg)
    
    print(cmd)
    subprocess.call(cmd,shell=True)

