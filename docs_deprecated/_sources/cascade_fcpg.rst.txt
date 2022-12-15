Cascade FCPG results between geospatial tiles
=============================================

Watersheds or hydrologic units, e.g. the `Watershed Boundary Dataset <https://www.usgs.gov/core-science-systems/ngp/national-hydrography/watershed-boundary-dataset?qt-science_support_page_related_con=4#qt-science_support_page_related_con>`_, are often used as geospatial tiling schemes for digital elevation models. These pose a challenge for FCPGs as downstream accumulated area and parameter grids must be corrected with values from upstream geospatial tiles to be accurate. This section contains examples for cascading flow between HUC4s and larger HUC2s or other geospatial tiling schemes.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   four_digit
   two_digit