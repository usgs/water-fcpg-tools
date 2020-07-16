Welcome to Flow-Conditioned Parameter Grid Tools' documentation!
=================================================================
The Flow-Conditioned Parameter Grid (FCPG) Tools are a Python 3 library to make FCPGs for either two-digit Hydrologic Unit Code (HUC2) regions, four-digit Hydrologic Unit Code (HUC4) regions, or other geospatial tiling schemes. These tools can be used in a Linux-based high performance computing (HPC) environment or locally on your system.

.. figure:: ../img/CPG_tool_structure.png
	:scale: 50 %
	:alt: Conceptual FCPG process flowchart.

	Flowchart of FCPG processing work flow.


Installation
============
Clone the repository using :code:`git clone https://code.usgs.gov/StreamStats/FCPGtools.git`.

Then change directories, using :code:`cd`, into the repository and create an Anaconda environment using the supplied :code:`FCPGtools_env.yml` file by calling :code:`conda env create -f FCPGtools_env.yml`. Activate the FCPG environment using the instructions printed by conda after the environment is created successfully.

Then, install the repository using :code:`pip install git+file:<Full Path to the FCPGtools repository>`

For example, :code:`pip install git+file:/home/<username>/projects/FCPGtools`

On a HPC system you may need to load the correct Python module before building the Anaconda environment. This might be done with :code:`module load python/anaconda3`.

Dependencies
============

Dependencies for this work are largely taken care of via the Anaconda environment specified by the yml file; however, the tools do rely on `TauDEM 5.3.8 <https://github.com/dtarb/TauDEM/tree/v5.3.8>`_ :cite:`TauDEM`, which needs to be installed and visible to your conda environment.

This library works best with GeoTiff files; however, other GDAL-compatible geospatial raster format could also potentially be used. 

Quick Start
===========
Load the FCPGtools using :code:`import FCPGtools as fcpg`.

Please refer to the :ref:`cookbook-label` and :ref:`function-label` for examples and usage.

Citation
========

Barnhart, T.B., Sando, R., Siefken, S.A., McCarthy, P.M., and Rea, A.H., 2020, Flow-Conditioned Parameter Grid Tools: U.S. Geological Survey Software Release, DOI: https://doi.org/10.5066/P9FPZUI0

Disclaimers
===========

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.

This software has been approved for release by the U.S. Geological Survey (USGS). Although the software has been subjected to rigorous review, the USGS reserves the right to update the software as needed pursuant to further analysis and review. No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. Furthermore, the software is released on condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from its authorized or unauthorized use.

License
=======

This work is published with the MIT Open Source License:

Copyright 2020 Theodore Barnhart, Roy Sando, Seth Siefken, Peter McCarthy, and Alan Rea (U.S. Geological Survey)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.