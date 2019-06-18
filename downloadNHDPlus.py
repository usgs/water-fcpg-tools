from tools import *

#HUClist = ["1005", "1006", "1007", "1008", "1009", "1010", "1011", "1012"]

HUClist = ["1013"]
fileDir = "../data/NHDPlus"

"""
for HUC in HUClist:
    downloadNHDPlusRaster(HUC, fileDir)
"""

from functools import partial
pool = processPool()

# Use pool.map() to download in parallel
pool.map(partial(downloadNHDPlusRaster, fileDir=fileDir), HUClist)

#close the pool and wait for the work to finish
pool.close()
pool.join()