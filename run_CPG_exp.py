import time
strt = time.time()
from tools import *
import sys
import geopandas as gpd

sampleIDX = sys.argv[1]

# make the CPG file first!

cov="./data/CHI_poster/daymet/daymet_v3_prcp_annttl_2017_na.tif"
taufdr="./data/CHI_poster/nhd/fdr_reclass.tif"
taufac="./data/CHI_poster/HRNHDPlusRasters1003/fac.tif"
workDir="./data/CHI_poster/cpg"
outDir="./data/CHI_poster/cpg"
cores=6
accumThresh=1000
overwrite=True
deleteTemp=False
HUC=str(1003)
outfl = "./data/CHI_poster/CPG_results.csv"

paramName = os.path.splitext(os.path.basename(cov))[0] 

#Prepare some file paths to things which will be created
rprjFile = os.path.join(workDir, paramName + "_HUC" + HUC + "rprj.tif") #Create filepath for reprojected parameter file
accumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accum.tif") #Create filepath for accumulated parameter file
nodataFile = os.path.join(workDir, paramName + "_HUC" + HUC + "nodata.tif") #Create filepath for parameter no data file
nodataaccumFile = os.path.join(workDir, paramName + "_HUC" + HUC + "accumnodata.tif") #Create filepath for parameter accumulated no data file
CPGFile = os.path.join(outDir, paramName + "_HUC" + HUC +"_CPG.tif") #Create filepath for parameter CPG file

resampleParam(cov, taufdr, rprjFile, resampleMethod="bilinear", cores=cores) #Resample and reprojected parameter raster
accumulateParam(rprjFile, taufdr, accumFile, outNoDataRast=nodataFile, outNoDataAccum=nodataaccumFile, cores=cores) #Accumulate parameter
if os.path.isfile(nodataaccumFile):
    #If no data accumulation file was created, use it in call to create CPG
    make_cpg(accumFile, taufac, CPGFile, noDataRast=nodataaccumFile, minAccum=accumThresh) #Create parameter CPG
else:
    make_cpg(accumFile, taufac, CPGFile,  minAccum=accumThresh) #Create parameter CPG

# query the CPG file based on a shapefile...

df = gpd.read_file("./data/CHI_poster/sample_locs_%s.shp"%(sampleIDX)) # read in the points

df['mean'] = queryCPG(CPGFile,df.geometry)
del df['geometry']
df.to_csv('./data/CHI_poster/CPG_res_%s.csv'%sampleIDX,index=False)

totalTime = time.time() - strt

print("Built CPG and queried points in %s minutes."%(totalTime/60.))

if not os.path.isfile(outfl):
	with open(outfl,'w') as dst:
		dst.write('RunNum,Time\n')
		dst.write('%s,%s\n'%(sampleIDX,totalTime))
else:
	with open(outfl,'a') as dst:
		dst.write('%s,%s\n'%(sampleIDX,totalTime))