Migrating to `FCPGtools` Version 2.0
===================================

## New in Version 2.0
Version 2.0 of `FCPGtools` is a complete rebuild of Version 1.0. Backwards compatibility is not preserved, and many workflows have been significantly streamlined. We strongly recommend that users who are familiar with Version 1.0 refer to our [updated documentation site](https://usgs.github.io/water-fcpg-tools/index.html).

### Key Updates
* All functions output an in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object, allowing for functions to be strung together into performance-oriented pipelines.
    * [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects have a variety of powerful features and optimizations. For more information, please reference the library's [documentation](https://docs.xarray.dev/en/stable/getting-started-guide/why-xarray.html).
    * Rasters can still be saved to a local GeoTIFF file by providing a valid `.tif` path to `param:out_path`.
* All functions can now accept either local string paths, local [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) objects, or in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects.
* Multi-band parameter grids are now supported!
    * For example, passing a 12-month precipitation raster (where each month is a raster band) into [`fcpgtools.accumulate_parameter()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_parameter) will output a 12-band [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object.
* Conversion of flow direction raster (FDR) formats (i.e. ESRI -> TauDEM) is now automated behind-the-scenes.
* Support for multiple "terrain engines" gives users additional optionality and increases the resiliance to dependency deprecation (see [below](#using-the-engine-parameter)). 
    * Where necessary users can set `param:engine` to [`taudem`](https://hydrology.usu.edu/taudem/taudem5/) (default) or [`pysheds`](https://github.com/mdbartos/pysheds).
    * Note that the `pysheds` terrain engine is signifcantly more performant, but currently only supports [`accumulate_flow()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_flow) and [`accumulate_parameter()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_parameter).


### Using the `engine` parameter
As mentioned above, some functions now require a "terrain engine" to be specified through the `param:engine` parameter (i.e., [`accumulate_flow()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_flow)). Under the hood, we use a [Python Protocols](https://peps.python.org/pep-0544/)-based implementation that will raise an error if the specified terrain engine does not support the function being called. All of these functions have a valid default terrain engine, so an error will only be raised if the user chooses to override the default in a unsupported way. While this may seem redundant, it enables more "terrain engines" to be incorporated in the future (i.e. [`WhiteBox`](https://www.whiteboxgeo.com/manual/wbw-user-manual/book/introduction.html)) without altering the user experience in any way, other than the number of valid `engine` string arguments. 

## Mapping of Version 1.1 to Version 2.0 `FCPGtools` Functions

### I/O Functions
* `loadRaster()` -> **`load_raster()`**
* `getFeatures()` -> **`load_shapefile()`**

### Key Use-Case Functions
* `resampleParam()` -> **`align_raster()`**
* `tauFlowAccum()` -> **`accumulate_flow()`**
* `accumulateParam()` -> **`accumulate_parameter()`**
*  `make_fcpg()` -> **`make_fcpg()`**
* `maskStreams()` -> **`mask_streams()`**
* `dist2stream()` -> **`distance_to_stream()`**
* `makeDecayGrid()` -> **`make_decay_raster()`**
* `decayAccum()` -> **`decay_accumulation()`**
* `ExtremeUpslopeValue()` -> **`extreme_upslope_values()`**

### Pour Points / Cascade Functions
* `findLastFACFD()` -> **`find_fac_pour_point()`** Output is of type 
* `makePourBasins()` and `findPourPoints()` -> **`find_basin_pour_points()`**  
which uses a basin shapefile to find outflow points. 
    * Output is of type `custom_types.PourPointLocationsDict`.
    * Note: In V2 `find_fac_pour_point()` gets the location of the outflow 
    point for a full FAC, which is then fed into `_find_downstream_cell()` 
    within `_update_raster_values()`. 
* `createUpdateDict()` -> **`get_pour_point_values()`**
    * The output is of type `custom_types.PourPointValuesDict`.
    * Note: The pour points workflow is somewhat different in V2, where the 
    output of either `find_basin_pour_points()` or `find_fac_pour_point()` 
    is appended with the pour point values within `get_pour_point_values()`. 
    
------------
### Functions made redundant but still accesible
* `makeFACweight()` -> `make_fac_weights()`
* `adjustParam` -> `adjust_parameter_raster()`
* `d8todinfinity()` -> `d8_to_dinfinity()`
* `tauDrainDir()` and `ESRIDrainDir()` -> `convert_fdr_formats()`
    * Note: FDR format conversion is now done automatically behind-the-scenes.
    * See `custom_types.D8ConversionDicts` for FDR format mappings.

### Functions moved to `fcpgtools.utilities` (wrapped into higher level functions)
* `FindDownstreamCellTauDir()` -> `_find_downstream_cell()`
* `changeNoData()` -> `_change_nodata_value()`
* `queryPoint()` -> `_query_point()`
* `updateRaster()` -> `_update_raster_values()`

------------------
### Completely removed functions (no longer necessary for use-cases)
*  `resampleParam_batch()`, `accumulateParam_batch()`, and `make_fcpg_batch()` 
are made redundant in V2 by utilizing f(x, y, t) rasters via `xarray.DataArray` 
objects.
* `makeStreams()` -> made redundant by `mask_streams()`.
* `cat2bin()` and `binarizeCat()` are combined into `binarize_categorical_raster()` 
by utilizing f(x, y, t) rasters via `xarray.DataArray` objects.
* `parsebool()` -> not necessary in V2.
* `applyMult()` -> not necessary in V2.