import FCPGtools as fcpg # Import the tools. 
import geopandas as gpd

# Define the file input and output paths and the upstream region.
upstreamFACfltau = '' # Upstream flow accumulation grid from TauDEM.
upstreamFDRfltau = '' # Upstream flow direction grid in TauDEM format.
downstreamFACfltau = '' # Downstream flow accumuation grid from TauDEM.
downstreamFDRfltau = '' # Downstream flow direction grid in TauDEM format.
region = '' # Hydrologic region to make the update dictionary for.
updateDict = '' # Path to the update dictionary to create.
downstreamFACWeight = '' # Path to the downstream FAC weighting grid. This is where the upstream value will be inserted.
downstreamAdjFAC = '' # Path to output the adjusted FAC weighting grid.
wbdPth = '' # Path to the watershed boundary dataset for the HUC-2 region you are working in.
dstCRS = '' # Proj4 represenation of the projection that the FCPGs will be in.
cores = 6 #Number of cores to use for fcpg.adjustFAC() function

# Define upstream and downstream basins.
upstream = ''
downstream = ''

# Load the WBD.
layer = 'WBDHU12' # HUC12 WBD layer with ToHUC codes.
wbd = gpd.read_file(wbdPth, layer = layer) # Load the WBD to a geodataframe.

# Convert HUC12 and ToHUC codes to 4-digit codes.,
wbd['HUC4'] = wbd.HUC12.map(fcpg.getHUC4)
wbd['ToHUC4'] = wbd.ToHUC.map(fcpg.getHUC4)

# Find basins that contain pour points.
pourBasins = fcpg.makePourBasins(wbd,upstream,downstream)

# Find pour points between the upstream and downstream basins.
pourPoints = fcpg.findPourPoints(pourBasins, upstreamFACfltau, upstreamFDRfltau, plotBasins = True)

# create update dictionary from the pour points.
newX,newY,maxFAC = zip(*pourPoints)
fcpg.createUpdateDict(newX,newY,maxFAC,upstream,updateDict)

# Update the downstream basin using the update dictionary.
fcpg.adjustFAC(downstreamFACfltau,downstreamFACWeight,updateDict,downstreamFDRfltau,downstreamAdjFAC, cores=cores) # note that this tool will create downstreamFACWeight if it does not exist based on downstreamFACfltau, see function documentation.
