import FCPGtools as fcpg

cores = 6 # Computer cores to use.
fdr = '' # Input ESRI flow direction grid.
fdrTau = '' # Output TauDEM formatted flow direction grid.
facTau = '' # Output flow accumulation grid.
    
fcpg.tauDrainDir(fdr, taufdr) # Reclassify flow directions.
fcpg.tauFlowAccum(taufdr, taufac, cores=cores) # Compute flow accumulation.