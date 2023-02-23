************************************
Welcome to FCPGtools Documentation!
************************************

`Flow-Conditioned Parameter Grid Tools (``FCPGtools``) <https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools>`_ 
is a Python 3 library that enables users to quickly create a flow-conditioned parameter 
grids (FCPG), as well other gridded output datasets, for use in statistical, 
machine learning, and physical hydrologic modeling. FCPGtools can be used in 
a Linux-based high performance computing (HPC) environment or locally on your 
system.

FCPGtools are used to analyze gridded parameter datasets -- 
such as precipitation, slope, or land use -- relative to a 
Flow Direction Grid/Raster (FDG/FDR) derived from terrain analysis, 
to generate seamless FCPG raster outputs. 
Each cell in these outputs stores a value that statistically summarizes 
parameter values for all cells that are upstream, upflow, or uphill.

More specifically, an FCPG is a pre-processing output that stores the **upstream 
statistics of parameter datasets for each grid cell in a landscape**. 
These tools allow you to store the upstream maximum and minimum parameter values, 
or to generate a FCPG with a decay factor that modifies the downstream 
accumulation calculation of the parameter.

For example, you could use these tools to calculate the average upstream 
precipitation value for each grid cell in a raster, or the maximum and minimum 
upstream slope values using a hillslope raster as the input parameter grid.

.. image:: ../img/flow_chart_image.png
   :width: 800

These types of gridded outputs are useful in a variety of hydrologic modeling 
applications and can serve as powerful predictive features in machine learning 
training datasets. This software package has previously been used to generate a 
seamless dataset of common basin characteristics for the contiguous United States, 
including mean upstream elevation, slope, minimum and maximum monthly temperature, 
annual precipitation, land cover class, and latitude.


Use and Citation
================
The FCPG Tools released to the public domain as they are produced by 
employees of the U.S. Government in collaboration with private sector partners. 
If you use these tools in your work, we request that you cite our publication 
along with a code citation for the release you are using. This helps us ensure that the 
contributions of the team behind the FCPG Tools are properly recognized, and 
will help justify the continued maintenance of this library.

Publication
------------
Barnhart, T.B., Schultz, A.R., Siefken, S.A., Thompson, F., Welborn, T., 
Sando, T.R., Rea, A.H., McCarthy, P.M., 2021, Flow-Conditioned Parameter 
Grids for the Contiguous United States: A Pilot, Seamless Basin Characteristic 
Dataset: U.S. Geological Survey data release, https://doi.org/10.5066/P9HUWM6Q.



Code Citation
--------------
`FCPGtools releases <https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/releases>`_ 
are commonly assigned authorship in the order of number of contributions. Example citations
are provided below.

* **Version 2.0.2** was released February, 2023.
    * Siefken, S.A., X.R. Nogueira, T.B. Barnhart, A.K. Aufenkampe, A.R. Schultz, 
      P. Tomasula. 2023. Flow-Conditioned Parameter Grid Tools Version 2.0.2. 
      https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/releases/v2.0.2.
* **Version 1.1.0** was released September, 2022.  
    * Siefken, S.A., T.B. Barnhart, A.R. Schultz, A.K. Aufenkampe, X.R. Nogueira. 2023. 
      Flow-Conditioned Parameter Grid Tools Version 1.1.1. 
      https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/releases/v1.1.1. 
* **Version 1.0** (IP-112996) was approved on September 3, 2020.
    * Siefken, S.A., T.B. Barnhart. 2020, Flow-Conditioned Parameter Grid Tools 
      version 1.0.  https://doi.org/10.5066/P9W8UZ47

If you encounter and issues with this software, please bring it to our attention 
by filling out a 
`GitLab Issues Form <https://code.usgs.gov/StreamStats/FCPGtools/-/issues/new?issuable_template=new_project>`_.


.. toctree::
    :maxdepth: 2
    :caption: Contents

    getting_started
    cookbook
    migrating_from_v1
    functions
    custom_types
    terrain_engine
    contributions
    publications
    z_references


Site Index
-----------
* :ref:`genindex`
