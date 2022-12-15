Cascade Four-Digit Hydrologic Regions
=====================================

This script provides an example work flow of how to cascade the last (maximum) accumulated area values from an upstream basin, e.g. HUC 1002 -- Upper Missouri, to the first cell of a downstream basin, e.g. HUC 1003 -- Missouri-Marias. The process creates a json file containing the values to be cascaded, creates a weighting grid of ones for the downstream region, inserts the upstream value into the weighting grid at the correct location, and accumulates the weighting grid using the downstream flow direction grid to produce an adjusted flow accumulation grid for the downstream region. This process can be repeated for each parameter grid and then used with :py:func:`make_fcpg` to create FCPGs corrected for upstream basins.

Example HUC-4 Cascading Work Flow
---------------------------------
.. literalinclude:: ../scripts/cascade_huc4.py
	:language: Python
	:linenos: