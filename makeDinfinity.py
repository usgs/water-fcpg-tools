from tools import *

HUClist = ["1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]


outDir = "../data/tauDEM"

cores = 16

for HUC in HUClist:

    DEM = "../data/NHDPlus05_06_2019/HRNHDPlusRasters{0}/elev_cm.tif".format(HUC)
    tauDINFfdr = os.path.join(outDir, "tauDINFfdr" + HUC + ".tif")
    taufac = os.path.join(outDir, "taufac" + HUC + ".tif")
    
    tauDrainDir(fdr, taufdr)
    tauFlowAccum(taufdr, taufac, cores=cores)

    try:
        print('Accumulating Data...')
        tauParams = {
        'fdr':fdr,
        'cores':cores, 
        'outFl':accumRast, 
        }
        
        cmd = 'mpiexec -bind-to rr -n {cores} aread8 -p {fdr} -ad8 {outFl} -nc'.format(**tauParams) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        

    except:
        print('Error Accumulating Data')
        traceback.print_exc()


