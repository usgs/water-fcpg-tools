.._migration-label:

New in Version 2.0
=====================================
Version 2.0 of `FCPGtools` is a ground-up refactor and rebuild of Version 1.0. 
Backwards compatibility is broken, and many work-flows have been significantly 
streamlined. We strongly suggest that any users accustomed to Version 1.0 
reference our [updated documentation site](TODO: LINK DOCUMENTATION SITE).

**A non-exhaustive list of key updates is below:**
* All functions output an in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object, allowing for functions to be strung together into performance oriented pipelines.
    * [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects have a variety of powerful features and optimizations. For more information please reference the library's [documentation](https://docs.xarray.dev/en/stable/getting-started-guide/why-xarray.html).
    * Rasters can still be saved to a local GeoTIFF file by providing a valid `.tif` path to `param:out_path`.
* All functions can now accept either local string paths, local [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) objects, or in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects.
* Multi-band parameter grids are now supported!
    * Example: Passing a 12-month precipitation raster (where each month is a raster band) into [`fcpgtools.accumulate_parameter()`](TODO: ADD LINK TO FUNTION DOCS HERE) will output a 12-band [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object.
* Flow Direction Raster format conversion (i.e. ESRI -> TauDEM) is now automated behind-the-scenes.
* Support for multiple "terrain engines" gives users optionality and increases dependency deprecation resiliancy. 
    * Where necessary users can set `param:engine` to [`taudem`](https://hydrology.usu.edu/taudem/taudem5/) (default) or [`pysheds`](https://github.com/mdbartos/pysheds).
    * Note that the `pysheds` terrain engine is signifcantly more performant, however it currently only supports [`accumulate_flow()`](TODO: ADD LINK TO FUNTION DOCS HERE) and [`accumulate_parameter()`](TODO: ADD LINK TO FUNTION DOCS HERE).

**Please reference our markdown [`refactored_names`](examples/refactored_names.md) document for a complete mapping of Version 1.1 to Version 2.0 function names.**