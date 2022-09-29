Welcome to Flow-Conditioned Parameter Grid Tools' documentation!
=================================================================
The Flow-Conditioned Parameter Grid (FCPG) Tools are a Python 3 library to make FCPGs for either two-digit Hydrologic Unit Code (HUC2) regions, four-digit Hydrologic Unit Code (HUC4) regions, or other geospatial tiling schemes. These tools can be used in a Linux-based high performance computing (HPC) environment or locally on your system.

.. figure:: ../img/CPG_tool_structure.png
	:scale: 50 %
	:alt: Conceptual FCPG process flowchart.

	Flowchart of FCPG processing work flow.

Use
===

The FCPG Tools are part of the public domain because they are produced by employees of the U.S. Government. However, if you use these tools I ask that you please let me know of any projects or publications that arise from their use. This allows me to justify the upkeep of this package and add citations to :ref:`pubs-label`.

Please cite the latest release of the code in any work that uses these tools (see the Citation Section below). If you receive support from me on your project or publication using the tools I ask that you acknowledge that support via a note in the acknowledgments or co-authorship.

Please use this `Issues Form <https://code.usgs.gov/StreamStats/FCPGtools/-/issues/new?issuable_template=new_project>`_ to alert me of new projects or publications using the tools. 

Citation
========

Barnhart, T.B., Sando, R., Siefken, S.A., McCarthy, P.M., and Rea, A.H., 2020, Flow-Conditioned Parameter Grid Tools: U.S. Geological Survey Software Release, DOI: https://doi.org/10.5066/P9W8UZ47.

Version 1.0 (IP-112996) was approved on September 3, 2020.
Version 1.1 was released in September, 2022.

Issues
======

Please log any issues with the repository here using `This Form <https://code.usgs.gov/StreamStats/FCPGtools/-/issues/new?issuable_template=bug>`_.

Documentation
=============

The documentation for this library is available at https://usgs.github.io/water-fcpg-tools/.

Dependencies
============

Dependencies for this work are best managed by the `conda <https://docs.conda.io/en/latest/>`_ package manager, with primary dependencies listed in the `FCPGtools_env.yml <https://code.usgs.gov/StreamStats/FCPGtools/-/raw/master/FCPGtools_env.yml>`_ environment file. 

FCPGtools relies on `TauDEM <https://github.com/dtarb/TauDEM/tree/v5.3.8>`_ :cite:`TauDEM` as the terrain analysis engine. The `FCPGtools_env.yml` will install TauDEM v5.3.8 for Windows and Linux.  For Mac, TauDEM 5.3.7 or greater will need to be installed separately and be visible to your conda environment. 

This library works best with GeoTIFF files; however, other GDAL-compatible geospatial raster format could also potentially be used. 

Installation
============

FCPGtools is designed to work with Python 3.7, 3.8, and 3.9.

To install, follow these three steps to create a `conda <https://docs.conda.io/`_ environment and run as a developer:

1. Install the Anaconda Python Distribution or Miniconda
---------
We recommend installing the `latest release <https://docs.anaconda.com/anaconda/reference/release-notes/>`_ of `**Anaconda Individual Edition** <https://www.anaconda.com/distribution>`_, which includes conda, a complete Python (and R) data science stack, and the helpful Anaconda Navigator GUI.
- Follow `Anaconda Installation <https://docs.anaconda.com/anaconda/install/>`_ documentation.

A lighter-weight alternative is to install `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_.

2. Clone or Download this FCPGtools repository
---------
From the `FCPGtools <https://code.usgs.gov/StreamStats/FCPGtools/>`_ GitLab page, download or clone this repository  using the  button on the near the upper right of the repo's landing page.

To most easily receive updates, we recommend cloning the repo using a git client, such as GitHub Desktop (which works on GitLab repos via the "Clone with HTTPS" function). 

3. Create the FCPGtools Conda Environment
---------
Create an `conda <https://docs.conda.io/en/latest/>`_ environment using the supplied :code:`FCPGtools_env.yml` file by calling :code:`conda env create -f FCPGtools_env.yml`. 
**Activate the FCPG environment using the instructions printed by conda after the environment is created successfully.**

4. Add your FCPGtools Path to Anaconda sites-packages
---------
To have access to the FCPGtools modules in your Python environment, it is necessary to have a path to your copy of FCPGtools in the :code:`sites-packages` directory of your conda environment (i.e. something like :code:`$HOME/path/to/anaconda/lib/pythonX.X/site-packages` or :code:`$HOME/path/to/anaconda/lib/site-packages` similar).

- The easiest way to do this is to use the `conda develop`<https://docs.conda.io/projects/conda-build/en/latest/resources/commands/conda-develop.html`_ command in the console or terminal like this, replacing :code:`/path/to/module/` with the full file pathway to the local cloned HSPsquared repository:

:code:`conda-develop /path/to/module/`

You should now be able to run the Tutorials and create your own Jupyter Notebooks!

If you cloned the repo, you will be able to switch branches to run different versions.


Quick Start
===========
Load the FCPGtools using :code:`import FCPGtools as fcpg`.

Please refer to the :ref:`cookbook-label` and :ref:`function-label` for examples and usage.

Disclaimers
===========

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.

Please see DISCLAIMER.md in the project repository. 

License
=======

Please see LICENSE.md in the project repository.
