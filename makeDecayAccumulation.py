import os
import subprocess
import traceback

#HUClist = ["1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]
HUClist = ["1002"]

outDir = "../data/tauDEM"

cores = 20

for HUC in HUClist:

    DEM = "../data/NHDPlus05_06_2019/HRNHDPlusRasters{0}/elev_cm.tif".format(HUC)
    tauDINFang = os.path.join(outDir, "tauDINFang" + HUC + ".tif")
    tauDINFslp = os.path.join(outDir, "tauDINFslp" + HUC + ".tif")
    

    try:
        print('Accumulating Data...')

        
        cmd = 'mpiexec -bind-to rr -n {0} dinfdecayaccum -ang {1} -dm {2} -dsca {3}'.format(cores, ang, mult, decayAccum) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        

    except:
        print('Error Accumulating Data')
        traceback.print_exc()


