#from builtins import range
import time
import arcpy
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *
import os
import sys

def delineate(numIter):
	loadStrt = time.time()
	numIter = int(numIter)

	#numIter = int(sys.argv[1]) # number of samples to run 
	#outfl = sys.argv[2] # output file location

	arcpy.env.workspace = "C:\\Users\\tbarnhart\\projects\\CPGtools\\data\\CHI_poster"

	outfl = os.path.join(arcpy.env.workspace,"ESRI_results.csv")

	fdrPath = os.path.join(arcpy.env.workspace,'HRNHDPlusRasters1003\\fdr.tif')
	paramPath = os.path.join(arcpy.env.workspace,'daymet\\daymet_v3_prcp_annttl_2017_na_reproj.tif')

	arcpy.env.extent = fdrPath
	arcpy.env.snapRaster = fdrPath
	arcpy.env.cellSize = fdrPath
	arcpy.env.overwriteOutput = True 

	fdr = Raster(fdrPath) # load the FDR
	param = Raster(paramPath) # load the parameter

	strt = time.time()
	arcpy.AddMessage("Run %s"%(numIter))

	outFeat = 'watersheds_%i.shp'%(numIter) # path to the output shapefile
	samples = 'sample_locs_%i.shp'%(numIter)

	delineationPath = "ESRI_delineation_%i.tif"%(int(numIter)) # path tou output raster

	if arcpy.Exists("ESRI_res_%i.dbf"%(numIter)):
		arcpy.Delete_management("ESRI_res_%i.dbf"%(numIter))

	if arcpy.Exists(outFeat):
		arcpy.Delete_management(outFeat)

	if arcpy.Exists(delineationPath):
		arcpy.Delete_management(delineationPath)

	PP = 'pp.tif'
	arcpy.FeatureToRaster_conversion(samples,"idx",PP,10)
	delineation = Watershed(fdr, PP) # compute watershed

	delineation.save(delineationPath)

	arcpy.AddMessage("	Computing Zonal Stats.")
	outStats = ZonalStatisticsAsTable(delineation,"Value", param,"ESRI_res_%i.dbf"%(numIter),"DATA","MEAN")

	runTime = time.time() - strt
	arcpy.AddMessage("	Run time: %s minutes."%(runTime/60.))

	arcpy.AddMessage("	Writing Output to : %s"%outfl)
	if not os.path.isfile(outfl):
	 	with open(outfl,'w') as dst:
	 		dst.write('RunNum,Time\n')
	 		dst.write('%s,%s\n'%(numIter,runTime))
	else:
	 	with open(outfl,'a') as dst:
	 		dst.write('%s,%s\n'%(numIter,runTime))
	arcpy.AddMessage("	Output Complete.")

	return runTime