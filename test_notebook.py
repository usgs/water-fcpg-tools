#!/usr/bin/env python
# coding: utf-8

# # FCPG Test Notebook
# 
# This notebook facilitates testing the the core functionality of the FCPG tools. This steps through providing input data, converting ESRI flow directions to TauDEM flow direction, resampling and reprojecting input data, generating upstream FCPGs, creating a dictionary to cascade values from upstream to downstream hydrologic units, updating downstream parameter grids, accumulating updated grids, and making FCPGs corrected for an upstream area. The last section verifies the handling of no data values if that is desired by the user.
# 
# This notebook reads data from `./test_data` and writes data to `./test_output`. `./test_output` can be discarded after testing is complete.
# 
# Input and output grids can be examined in either ArcGIS or QGIS.

# In[1]:


import FCPGtools as fc
import os
import rasterio as rs
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# Verbose output
verbose = True

def plot(fl, cmap='Blues'): # define a helper plotting function
	src = rs.open(fl)
	tmp = src.read(1)
	try:
		tmp[tmp == src.nodata] = np.NaN
	except:
		pass
	plt.figure(figsize = (10,10))
	plt.imshow(tmp, cmap = cmap)

print('FCPGtools version %s loaded from %s'%(fc.__version__,fc.__path__[0]))


# In[4]:


# input data sets
upstreamFDR = os.path.join('.','test_data','validation_upstream_fdr.tif') # upstream area FDR grid
downstreamFDR = os.path.join('.','test_data','validation_downstream_fdr.tif') # downstream area FDR grid
upstreamWBD = gpd.read_file(os.path.join('.','test_data/upstream_wbd.shp')) # upstream WBD subset to test cascading parameters


# parameter datasets
P = os.path.join('.','test_data','validation_daymet_an_P_2017.tif') # daymet annual P for 2017
LC = os.path.join('.','test_data','NALCMS_2015.tif') # North America Land Cover 2015

testFolder = os.path.join('.','test_output') # folder to store outputs


# In[5]:


# reproject the WBD to the grid CRS
tmp = rs.open(upstreamFDR)
dstCRS = tmp.crs.to_proj4()

upstreamWBD.to_crs(crs=dstCRS, inplace=True)


# In[6]:


if os.path.exists(testFolder) == False: # make test output location if it doesn't exist, this directory can be deleted later
	os.mkdir(testFolder)


# ## Convert ESRI FDR to TauDEM FDR

# In[7]:


# define output paths
upstreamFDRTau = os.path.join(testFolder,'upstreamFDRtau.tif')
downstreamFDRTau = os.path.join(testFolder,'downstreamFDRtau.tif')


# In[8]:


# reclassify ESRI drainage directions to TauDEM
fc.tauDrainDir(upstreamFDR, upstreamFDRTau, verbose=verbose)
fc.tauDrainDir(downstreamFDR, downstreamFDRTau, verbose=verbose)


# ## Resample Daymet and Land Cover

# In[9]:


# define output paths
Pupstream = os.path.join(testFolder,'Pup.tif')
Pdownstream = os.path.join(testFolder,'Pdwn.tif')
LCupstream = os.path.join(testFolder,'LCup.tif')
LCdownstream = os.path.join(testFolder,'LCdwn.tif')


# In[11]:


fc.resampleParam(P,upstreamFDRTau, Pupstream, cores=4, forceProj = True, verbose=verbose) # resample and crop daymet upstream
fc.resampleParam(P,downstreamFDRTau,Pdownstream, cores=4, forceProj = True, verbose=verbose) # downstream
fc.resampleParam(LC, downstreamFDRTau, LCdownstream, cores=4, forceProj = True, verbose=verbose, resampleMethod = 'near')
fc.resampleParam(LC, upstreamFDRTau, LCupstream, cores=4, forceProj = True, verbose=verbose, resampleMethod = 'near')


# ## Binarize Land Cover

# In[9]:


usLCbinary = fc.cat2bin(LCupstream, testFolder, verbose=verbose)
dsLCbinary = fc.cat2bin(LCdownstream, testFolder, verbose=verbose)


# ## Accumulate the Upstream Area

# In[10]:


upstreamFAC = os.path.join(testFolder,'upstreamFAC.tif') # path for the output FAC grid.

fc.tauFlowAccum(upstreamFDRTau,upstreamFAC, cores=1, mpiCall = 'srun', mpiArg = '-n', verbose=verbose)


# In[11]:


plot(upstreamFAC)


# ## Demonstration of Multiple Pour Points
# 
# The following is a demonstration of the workflow for HUC4 geospatial tiles (NHD High-Res). The update dictionary produced here is not used after this Section.

# In[12]:


upstreamWBD


# In[13]:


pourBasins = fc.makePourBasins(upstreamWBD,'1407','1501')
pourPts = fc.findPourPoints(pourBasins,upstreamFAC, upstreamFDRTau, plotBasins=True)


# In[14]:


pourPts


# In[15]:


# create an initial dictionary for the region 14 to 15 cascade
updateDictFl = os.path.join(testFolder,'HUC1407_update.json')
upHUC = '1407'
x,y,w = zip(*pourPts) # expand the pour points

ud = fc.createUpdateDict(x,y,w,upHUC, updateDictFl, verbose = verbose)


# In[16]:


ud # there are two pour points


# ## Find Pour Point to Downstream Area

# In[17]:


# find the single pour point between region 14 and region 15.
x,y,d,w = fc.findLastFACFD(upstreamFAC, fl = upstreamFAC) # locate max FAC value.
x,y,f,w = fc.findLastFACFD(upstreamFAC, fl = upstreamFDRTau) # Get flow direction of above point


# In[18]:


# create an initial dictionary for the region 14 to 15 cascade
updateDictFl = os.path.join(testFolder,'HUC14_update.json')
upHUC = '14'
ud = fc.createUpdateDict([x],[y],[d],upHUC, updateDictFl, verbose = verbose)


# ## FCPG Upstream Daymet and Land Cover

# In[19]:


usLCbinary.append(Pupstream) # append the Daymet path to the land cover binary grids


# In[20]:


accumParams = fc.accumulateParam_batch(usLCbinary,upstreamFDRTau,testFolder,cores = 4, verbose = verbose)


# In[21]:


upstream_cpgs = fc.make_fcpg_batch(accumParams,upstreamFAC,testFolder, verbose = verbose)


# ### Create Update Dictionary with FCPG Values

# In[22]:


# Update the dictionary with values from the upstream accumulated parameters, this should probably be a v2 function...
for fl in accumParams: # iterate through the accumulated parameters
	print(fl)
	# Parse the file names into variable names... 
	varname = fl.split('/')[-1].split('up')[0]
	if varname == 'LC':
		mod = fl.split('/')[-1].split('up')[-1].split('accum')[0]
		var = varname+mod
	else:
		var = varname
	
	# Query accumualted raster for values
    
	val = str(fc.queryPoint(x,y,fl))
    
	ud = fc.updateDict(updateDictFl,'14',var,[val])	


# ## Cascade to Downstream Area

# In[23]:


downstreamFACadj = os.path.join(testFolder,'downstreamFACadj.tif')
downstreamFACweight = os.path.join(testFolder,'downstreamFACweight.tif')
fc.adjustFAC(downstreamFDRTau,downstreamFACweight,updateDictFl,downstreamFDRTau,downstreamFACadj, cores = 4, verbose = verbose)


# In[24]:


dsLCbinary.append(Pdownstream) #add the precip into the downstream land cover files


# In[25]:


# create updated, unaccumulated parameter grids for the downstream region
adjDSparams = []
for fl,inGrid in zip(accumParams,dsLCbinary): # iterate through the accumulated parameters
	# Parse the file names into variable names... 
	varname = fl.split('/')[-1].split('up')[0]
	if varname == 'LC':
		mod = fl.split('/')[-1].split('up')[-1].split('accum')[0]
		var = varname+mod
	else:
		var = varname
	
	outfl = inGrid.split('.tif')[0]+'adj.tif'
    
	fc.adjustParam(var,inGrid,updateDictFl,outfl, verbose = verbose)
	adjDSparams.append(outfl)


# In[26]:


# accumulate the downstream parameter grids
DSaccum = fc.accumulateParam_batch(adjDSparams,downstreamFDRTau,testFolder, cores=4, verbose = verbose)


# In[27]:


# accumulate the downstream area
dsFCPG = fc.make_fcpg_batch(DSaccum,downstreamFACadj,testFolder, verbose = verbose)


# ## Insert NoData values into Daymet and Verify FCPG NoData Behavior 

# In[28]:


with rs.open(upstreamFDR) as src:
	fdr = src.read(1)
	fdr[fdr == src.nodata] = 0
	fdr[fdr != 0] = 1
	mask = fdr.astype(np.uint)


# In[29]:


plt.imshow(mask)


# In[30]:


#make row,col vectors of where to insert nodata values

size = 1000 # number of no data values to insert

idCol,idRow = np.where(mask == 1) # get locations of all points within the watershed

cols = np.random.choice(idCol,size = size,replace = False)
rows = np.random.choice(idRow, size = size, replace = False)


# In[31]:


PupstreamNoData = os.path.join(testFolder,'PupNoData.tif') # output file name

# open source
with rs.open(Pupstream) as src:
	meta = src.meta
	noData = src.nodata
	P = src.read(1)

P[cols,rows] = noData # insert nodata values

# write out updated P grid
with rs.open(PupstreamNoData,'w',**meta) as dst:
	dst.write(P,1)


# In[32]:


plt.imshow(P)


# In[33]:


# accumualte the P raster with no data values added and produce the noData grids

accumRast = os.path.join(testFolder,'PupNoData_accum.tif')
outNoDataAccum = os.path.join(testFolder,'PupNoData_accumNoData.tif')
outNoData = os.path.join(testFolder,'PupNodataRast.tif')
outNoDataZero = os.path.join(testFolder,'PupNoDataZero.tif')

fc.accumulateParam(PupstreamNoData, upstreamFDRTau, accumRast,
				   outNoDataRast = outNoData, outNoDataAccum=outNoDataAccum,
				   zeroNoDataRast = outNoDataZero ,cores = 4, verbose = verbose)


# In[34]:


# make a FCPG accounting for noData
outRast = os.path.join(testFolder,'Pup_FCPG_noData.tif')

fc.make_fcpg(accumRast,upstreamFAC, outRast, noDataRast=outNoDataAccum, verbose = verbose)


# ## Decay FCPG
# 
# Produce a FCPG where values are decayed based on their distance to a stream, this can be useful for producing FCPGs with more localized values rather than basin-average values.

# In[35]:


upstreamFDRTauDinf = os.path.join(testFolder,'upstreamFDRDinf.tif') # D-infinity flow direction raster
fc.d8todinfinity(upstreamFDRTau, upstreamFDRTauDinf, verbose = verbose) # convert D8 flow directions to D-inf flow directions


# In[36]:


streamDistRast = os.path.join(testFolder,'upstreamDist2Stream.tif') # distance to stream raster
streamRast = os.path.join(testFolder,'upstreamSTR900.tif') # stream raster
fc.makeStreams(upstreamFAC, streamRast, verbose = verbose)
fc.dist2stream(upstreamFDRTau, upstreamFAC, 900, streamDistRast, cores = 4, verbose = verbose) # compute distance to streams, use 900 cells as accumulation threshold 


# In[37]:


decayRast = os.path.join(testFolder,'upstreamDecay.tif')
k = 4 # decay coefficient
fc.makeDecayGrid(streamDistRast, k, decayRast, verbose = verbose)
plot(decayRast, cmap = 'Greens')


# In[38]:


decayFAC = os.path.join(testFolder,'decayAccum.tif') # decay accumulation grid
decayParam = os.path.join(testFolder,'decayP.tif') # decay parameter accumulation grid

fc.decayAccum(upstreamFDRTauDinf, decayRast, decayParam, # perform the parameter decay accumulation
			  paramRast = Pupstream, cores = 4, verbose = verbose)


# In[39]:


decayFCPG = os.path.join(testFolder,'decayFCPG.tif')
fc.maskStreams(decayParam, streamRast, decayFCPG, verbose = verbose) #Mask out pixels not on streamlines

