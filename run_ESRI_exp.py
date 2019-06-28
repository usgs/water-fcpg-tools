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

	sampLyr = 'sampLyr'
	PP = 'pp.tif'
	arcpy.MakeFeatureLayer_management(samples,sampLyr)

	loadTotal = time.time() - loadStrt

	tmp = Int(Con(IsNull(fdr)==0,0)) # make empty raster
	wshds = []
	with arcpy.da.SearchCursor(samples,['idx']) as cursor: # iterate through each point
		for field in cursor:
			arcpy.AddMessage('	Delineating watershed %i'%field[0])
			arcpy.SelectLayerByAttribute_management(sampLyr,"NEW_SELECTION",'"idx" = %s'%field[0])

			arcpy.FeatureToRaster_conversion(sampLyr,"idx",PP,10)

			wshd = Watershed(fdr, PP) # compute watershed
			tmp += Int(Con(IsNull(wshd)==0,int(field[0]),0)) # add the idx number to the delineation raster, before, this had nulls, wich was generating an all-null raster
			#wshds.append(Int(Con(IsNull(wshd)==0,int(field[0]),0)))
			arcpy.SelectLayerByAttribute_management(sampLyr,"CLEAR_SELECTION")

	#arcpy.MosaicToNewRaster_management(wshds,arcp.env.workspace, delineationPath, pixel_type="32_BIT_UNSIGNED", mosaic_method = "SUM")
	#delineation = Raster(delineationPath)
	delineation = Int(Con((IsNull(fdr)==0) & (tmp != 0),tmp,'')) # mask out the no data areas again.
	delineation.save(delineationPath)

	arcpy.AddMessage("	Computing Zonal Stats.")
	outStats = ZonalStatisticsAsTable(delineation,"Value", param,"ESRI_res_%i.dbf"%(numIter),"DATA","MEAN")

	runTime = time.time() - strt
	arcpy.AddMessage("	Run time: %s minutes."%(runTime/60.))

	#outfl = os.path.join(arcpy.env.workspace,outfl)

	# arcpy.AddMessage("	Writing Output to : %s"%outfl)
	# if not os.path.isfile(outfl):
	# 	with open(outfl,'w') as dst:
	# 		dst.write('RunNum,Time\n')
	# 		dst.write('%s,%s\n'%(numIter,totalTime))
	# else:
	# 	with open(outfl,'a') as dst:
	# 		dst.write('%s,%s\n'%(numIter,totalTime))
	# arcpy.AddMessage("	Output Complete.")

	return loadTotal, runTime