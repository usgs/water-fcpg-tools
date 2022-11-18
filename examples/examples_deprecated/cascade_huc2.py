import FCPGtools as fcpg # Import the tools. 

# Define the file input and output paths and the upstream region.
upstreamFDRflesri = '' # Upstream flow direction grid in ESRI format.
downstreamFDRflesri = '' # Downstream flow direction grid in ESRI format.
upstreamFACfltau = '' # Upstream flow accumulation grid from TauDEM.
upstreamFDRfltau = '' # Upstream flow direction grid in TauDEM format.
downstreamFACfltau = '' # Downstream flow accumuation grid from TauDEM.
downstreamFDRfltau = '' # Downstream flow direction grid in TauDEM format.
region = '' # Hydrologic region to make the update dictionary for.
updateDict = '' # Path to the update dictionary to create.
downstreamFACWeight = '' # Path to the downstream FAC weighting grid. This is where the upstream value will be inserted.
downstreamAdjFAC = '' # Path to output the adjusted FAC weighting grid.
cores = 8 #Number of cores to use for fcpg.adjustFAC() function

# convert ESRI flow directions to TauDEM flow directions.
fcpg.tauDrainDir(upstreamFDRflesri, upstreamFDRfltau)
fcpg.tauDrainDir(downstreamFDRflesri, downstreamFDRfltau)

# Accumulate upstream FDR grid.
fcpg.tauFlowAccum(upstreamFDRfltau, upstreamFACfltau)

# Create the update dictionary to move data between HUC2 regions.
x,y,d,w = fcpg.findLastFACFD(upstreamFACfltau, upstreamFACfltau)
fcpg.createUpdateDict(x,y,d,region,updateDict)

# Make a grid of ones based on the downstream grid.
fcpg.makeFACweight(downstreamFDRfltau,downstreamFACWeight)

# Create the updated flow accumulation grid with information from the upstream HUC inserted into the source grid.
fcpg.adjustFAC(downstreamFDRfltau,downstreamFACWeight,
              updateDict,downstreamFDRfltau,downstreamAdjFAC,cores=cores)
