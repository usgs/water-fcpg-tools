Comparison of V1 and Refactored V2 FCPGTools Functions (as of 12/7/2022)
========================================================================
* `parsebool()` -> not necessary in V2.
* `tauDrainDir()` and `ESRIDrainDir()` -> `convert_fdr_formats()`
    * Note: using `types.D8ConversionDicts` FDR formats can be converted using one function, and additional formats can be added by simply updating the dictionary mapping.
* `accumulateParam()` -> `accumulate_parameter()`
*  `make_fcpg()` -> `make_fcpg()`
* `resampleParam()` -> `align_raster()`
    * Note: Since this function has utility beyond just resampling a parameter raster (for example on could resample a FDR from a different source), we chose to generalize the name.
* `makeDecayGrid()` -> `make_decay_raster()`
* `applyMult()` -> not necessary in V2.
* `decayAccum()` -> `decay_accumulation()`
* `dist2stream()` -> `distance_to_stream()`
* `maskStreams()` -> `mask_streams()`
*  `resampleParam_batch()`, `accumulateParam_batch()`, and `make_fcpg_batch()` are made redundant in V2 by utilizing f(x, y, t) rasters via `xarray.DataArray` objects.
* `cat2bin()` and `binarizeCat()` are combined into `binarize_categorical_raster()` by utilizing f(x, y, t) rasters via `xarray.DataArray` objects.
* `tauFlowAccum()` -> `accumulate_flow()` which is possible via the `taudem_engine` or the `pysheds_engine`.
* `ExtremeUpslopeValue()` -> `extreme_upslope_values()`
* `getFeatures()` -> not necessart in V2, shapefiles can be loaded into `geopandas.GeoDataFrame` objects via `load_shapefile()`.
* `loadRaster()` -> `load_raster()`
* `queryPoint()` -> `_query_point()`
* `FindDownstreamCellTauDir()` -> `_find_downstream_cell()`
* `updateRaster()` -> `_update_raster_values()`
* `makeFACweight()` -> `make_fac_weights()`
* `adjustParam` -> `adjust_parameter_raster()`
* `d8todinfinity()` -> `d8_to_dinfinity()`
* `changeNoData()` -> `_change_nodata_value()`
* `makeStreams()` -> made redundant by `mask_streams()`.
* `makePourBasins()` and `findPourPoints()` -> `find_basin_pour_points()` which uses a basin shapefile to find outflow points. Output is of type `types.PourPointLocationsDict`.
* `findLastFACFD()` -> `find_fac_pour_point()` Output is of type `types.PourPointLocationsDict`.
    * Note: In V2 `find_fac_pour_point()` gets the location of the outflow point for a full FAC, which is then fed into `_find_downstream_cell()` within `_update_raster_values()`. 
* `createUpdateDict()` -> `get_pour_point_values()`
    * Note: The pour points workflow is somewhat different in V2, where the output of either `find_basin_pour_points()` or `find_fac_pour_point()` is appended with the pour point values within `get_pour_point_values()`. The output of `get_pour_point_values()` is of type `types.PourPointValuesDict`.