.. Flow-Conditioned Parameter Grid Tools documentation master file, created by
   sphinx-quickstart on Wed Mar 25 15:26:35 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flow-Conditioned Parameter Grid Tools's documentation!
=================================================================
A Python library to make flow-conditioned parameter grids (FCPGs) by either HUC2, HUC4, or other geospatial tiling schemes. These tools can be used in a Linux HPC environment or locally on your system. These tools are written for Linux and are tested for Windows 10 using the Window's Subsystem for Linux Ubuntu 18 LTS.

Quick Start
===========
Load the FCPGtools using :code:`import FCPGtools as fcpg`.

Installation
============
Clone the repository using :code:`git clone https://code.usgs.gov/StreamStats/FCPGtools.git`.

Then :code:`cd` into the repository and create a Anaconda environment using the supplied :code:`FCPGtools_env.yml` file by calling :code:`conda env create -f FCPGtools_env.yml`.

Then, install the repository using :code:`pip install git+file:<Full Path to the FCPGtools repository>`

For example, :code:`pip install git+file:/home/<username>/projects/FCPGtools`

On a HPC system you may need to load the correct Python module before building the Anaconda environment. This might be done with :code:`module load python/anaconda3`

Dependencies
============

Dependencies for this work are largely taken care of via the anaconda environment specified by the yml file; however, the tools do rely on `TauDEM 5.3.8 <https://github.com/dtarb/TauDEM/tree/v5.3.8>`_, which needs to be installed and visible to your conda environment.

Citation
========

Barnhart, T.B., Sando, T.R., Siefken, S.A., McCarthy, P.M., Rea, A.H. (2020). Flow-Conditioned Parameter Grid Tools. U.S. Geological Survey Software Release. DOI: https://doi.org/10.5066/P9FPZUI0


Disclaimers
===========

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.

This software has been approved for release by the U.S. Geological Survey (USGS). Although the software has been subjected to rigorous review, the USGS reserves the right to update the software as needed pursuant to further analysis and review. No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. Furthermore, the software is released on condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from its authorized or unauthorized use.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cookbook
   functions
   example_scripts
   glossary


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
