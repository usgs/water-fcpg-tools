import os
import subprocess
import traceback

#HUClist = ["1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012", "1013"]
HUClist = ["1002"]

outDir = "../data/tauDEM"

cores = 20

mult = "../data/tauDEM/mult1002.tif" #Decay multiplier

for HUC in HUClist:

    ang = "../data/tauDEM/tauDINFang{0}.tif".format(HUC)

    decayAccum = os.path.join(outDir, "tau050DecayAccum" + HUC + ".tif")
    

    try:
        print('Accumulating Data...')

        
        cmd = 'mpiexec -bind-to rr -n {0} dinfdecayaccum -ang {1} -dm {2} -dsca {3}'.format(cores, ang, mult, decayAccum) # Create string of tauDEM shell command
        print(cmd)
        result = subprocess.run(cmd, shell = True) # Run shell command
        
        result.stdout
        

    except:
        print('Error Accumulating Data')
        traceback.print_exc()


