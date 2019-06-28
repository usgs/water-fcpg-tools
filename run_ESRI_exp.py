import time
strt = time.time()

import arcpy
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *
import os
import sys

numSamples = sys.argv[1] # number of samples to run 
runNum = sys.argv[2] # run number
samples = sys.argv[3] # samples to run
outfl = sys.argv[4] # output file location

arcpy.env.workspace = r"C:/Users/tbarnhart/projects/CPGtools/data/CHI_poster"

fdrPath = 'HRNHDPlusRasters1003/fdr.tif'
paramPath = 'daymet_v3_prcp_annttl_2012_na.tif'

arcpy.env.extent = fdrPath
arcpy.env.snapRaster = fdrPath
arcpy.env.cellSize = fdrPath
arcpy.env.overwriteOutput = True 

sampLyr = "sampLyr"
arcpy.MakeFeatureLayer_management(samples, sampLyr)
#samp = arcpy.SelectLayerByAttribute_management(sampLyr, "NEW_SELECTION", '"idx" <= %i'%(numSamples))

fdr = Raster(fdrPath) # load the FDR
param = Raster(paramPath) # load the parameter

arcpy.AddMessage("Delineating watersheds for run: %s, %s points."%(runNum, numSamples))

delineation = Con(IsNull(fdr) == 0,0,'')
with arcpy.da.SearchCursor(samples,['idx']) as cursor: # loop through each point
	for field in cursor:
		samp = arcpy.SelectLayerByAttribute_management(sampLyr, "NEW_SELECTION", '"idx" = %i'%field[0]) # select each point
		delineation += Watershed(fdr,samp,"idx") # run the watershed and sum onto output raster
		arcpy.SelectLayerByAttribute_management(samp, "CLEAR_SELECTION") # start over

delineation = SetNull(IsNull(fdr),delineation)

delineation.save("ESRI_delineation_%i.tif"%(int(runNum)))

arcpy.AddMessage("Computing Zonal Stats for run: %s, %s watersheds."%(runNum, numSamples))
outStats = ZonalStatisticsAsTable(delineation,"Value", param,"ESRI_res_%i.dbf"%int(runNum),"DATA","MEAN")


totalTime = time.time() - strt
arcpy.AddMessage("run time: %s minutes."%(totalTime/60.))

outfl = os.path.join(arcpy.env.workspace,outfl)

arcpy.AddMessage("Writing Output to : %s"%outfl)
if not os.path.isfile(outfl):
	with open(outfl,'w') as dst:
		dst.write('RunNum,Time\n')
		dst.write('%s,%s\n'%(runNum,totalTime))
else:
	with open(outfl,'a') as dst:
		dst.write('%s,%s\n'%(runNum,totalTime))
arcpy.AddMessage("Output Complete.")