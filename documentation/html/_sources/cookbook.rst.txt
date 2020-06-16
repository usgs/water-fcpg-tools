.. _cookbook-label:

Cookbook
========

Example scripts and work flows for common FCPG tasks on local workstations and HPC environments. These scripts have not been turned into FCPGtools functions because of the variability in HPC, local systems, and input data sets that the FCPGtools may be used with.

Input Data
----------
To produce a basic FCPG you will need the following data for the same geographic area:
	- Flow direction grid, ideally with TauDEM flow directions. Other flow direction formats (e.g. ESRI) can be reclassified to TauDEM flow directions.
	- Parameter grid, a precipitation or air temperature grid is likely easiest, the resolution does not need to match your flow direction grid; however, the extent must be at least that of the flow direction grid.

To produce more complex FCPGs from categorical data or that cascade from one upstream hydrologic tile to a downstream tile you will need more data:
   - A categorical parameter grid (e.g. land cover).
	- The Watershed Boundary Dataset for the area you are working in. This helps the tools locate areas within geospatial tiles that flow out of the tile and into the next downstream tile.

.. toctree::
   :maxdepth: 2
   :caption: Examples:

   make_TauDEM_files
   batch_fcpgs_hpc
   cascade_fcpg
   detect_missing
   