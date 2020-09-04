Cascade Two-Digit Hydrologic Regions
====================================

This script provides an example work flow of how to cascade the last (maximum) accumulated area value from an upstream region, e.g. Region 14 -- Upper Colorado, to the first cell of a downstream region, e.g. Region 15 -- Lower Colorado. For this example, it is assumed that the user is working with ESRI-produced flow direction grids. Because of the differences in the encoding of flow directions calculated with ESRI tools and flow directions calculated with TauDEM, the FCPG tools require flow direction data to be converted to TauDEM encoding if they are not already. The process creates a json file containing the value to be cascaded, creates a weighting grid of ones for the downstream region, inserts the upstream value into the weighting grid at the correct location, and accumulates the weighting grid using the downstream flow direction grid to produce an adjusted flow accumulation grid for the downstream region. This process can be repeated for each parameter grid and then used with :py:func:`make_fcpg` to create FCPGs corrected for upstream regions.


Example HUC-2 Cascading Work Flow
---------------------------------
.. literalinclude:: ../scripts/cascade_huc2.py
	:language: Python
	:linenos: