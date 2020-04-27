Cascade Two-Digit Hydrologic Regions
====================================

This script provides an example work flow of how to cascade the last (maximum) accumulated area value from an upstream region, e.g. Region 14 -- Upper Colorado, to the first cell of a downstream region, e.g. Region 15 -- Lower Colorado. The process creates a json file containing the value to be cascaded, creates a weighting grid of ones for the downstream region, inserts the upstream value into the weighting grid at the correct location, and accumulates the weighting grid using the downstream flow direction grid to produce an adjusted flow accumulation grid for the downstream region. This process can be repeated for each parameter grid and then used with :py:func:`make_fcpg` to create FCPGs corrected for upstream regions.


Example HUC-2 Cascading Work Flow
---------------------------------
.. literalinclude:: ../scripts/cascade_huc2.py
	:language: Python
	:linenos: