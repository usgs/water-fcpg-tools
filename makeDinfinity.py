from tools import *

#HUClist = ["1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]
HUClist = ["1002"]

outDir = "../data/tauDEM"

cores = 4

for HUC in HUClist:

    DEM = "../data/NHDPlus05_06_2019/HRNHDPlusRasters{0}/elev_cm.tif".format(HUC)
    tauDINFang = os.path.join(outDir, "tauDINFang" + HUC + ".tif")
    tauDINFslp = os.path.join(outDir, "tauDINFslp" + HUC + ".tif")
    

    try:
        print('Accumulating Data...')

        
        cmd = 'mpiexec -bind-to rr -n {0} dinfflowdir -fel {1} -ang {2} -slp {3}'.format(cores, DEM, tauDINFang, tauDINFslp) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        

    except:
        print('Error Accumulating Data')
        traceback.print_exc()


