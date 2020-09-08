Welcome to Flow-Conditioned Parameter Grid Tools' documentation!
=================================================================
The Flow-Conditioned Parameter Grid (FCPG) Tools are a Python 3 library to make FCPGs for either two-digit Hydrologic Unit Code (HUC2) regions, four-digit Hydrologic Unit Code (HUC4) regions, or other geospatial tiling schemes. These tools can be used in a Linux-based high performance computing (HPC) environment or locally on your system.

.. figure:: ../img/CPG_tool_structure.png
	:scale: 50 %
	:alt: Conceptual FCPG process flowchart.

	Flowchart of FCPG processing work flow.

Please log any issues with the repository here: https://code.usgs.gov/StreamStats/FCPGtools/-/issues

Documentation
=============

The documentation for this library is available at https://usgs.github.io/water-fcpg-tools/.

Dependencies
============

Dependencies for this work are largely taken care of via the `Anaconda <https://www.anaconda.com/products/individual>`_  environment specified by the yml file; however, the tools do rely on `TauDEM <https://github.com/dtarb/TauDEM/tree/v5.3.8>`_ :cite:`TauDEM`, which needs to be installed and visible to your conda environment. Please install Anaconda Python 3 and TauDEM version 5.3.7 or greater prior to installing the Flow-Conditioned Parameter Grid Tools.

This library works best with GeoTIFF files; however, other GDAL-compatible geospatial raster format could also potentially be used. 

Installation
============
Clone the repository using :code:`git clone https://github.com/usgs/water-fcpg-tools.git`.

Then change directories into the repository and create an `Anaconda <https://www.anaconda.com/products/individual>`_ environment using the supplied :code:`FCPGtools_env.yml` file by calling :code:`conda env create -f FCPGtools_env.yml`. **Activate the FCPG environment using the instructions printed by conda after the environment is created successfully.**

Then, install the repository using :code:`pip install https://github.com/usgs/water-fcpg-tools`

On a HPC system you may need to load the correct Python module before building the Anaconda environment. This might be done with :code:`module load python/anaconda3`.

Upgrading
---------
Periodically, updates and bug fixes will be made to this library. To update your installation re-run :code:`pip install https://github.com/usgs/water-fcpg-tools`.

Quick Start
===========
Load the FCPGtools using :code:`import FCPGtools as fcpg`.

Please refer to the :ref:`cookbook-label` and :ref:`function-label` for examples and usage.

Citation
========

Barnhart, T.B., Sando, R., Siefken, S.A., McCarthy, P.M., and Rea, A.H., 2020, Flow-Conditioned Parameter Grid Tools: U.S. Geological Survey Software Release, DOI: https://doi.org/10.5066/P9W8UZ47.

Version 1.0 (IP-112996) was approved on September 3, 2020.

Disclaimers
===========

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.

Please see DISCLAIMER.md in the project repository. 

License
=======

Please see LICENSE.md in the project repository.
