import fcpgtools.tools_deprecated as fcpg

cores = 6  # Computer cores to use.
fdr = ''  # Input ESRI flow direction grid.
fdrTau = ''  # Output TauDEM formatted flow direction grid.
facTau = ''  # Output flow accumulation grid.

fcpg.tauDrainDir(fdr, fdrTau)  # Reclassify flow directions.
fcpg.tauFlowAccum(fdrTau, facTau, cores=cores)  # Compute flow accumulation.
