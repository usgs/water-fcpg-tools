Cookbook/Examples
=====================

Here we provide a few example work flows for common FCPG tasks.

## Input Data
To produce a basic FCPG you will need the following data for the same geographic area:

   * A Flow Direction Raster (FDR), either in [ESRI](https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/how-flow-direction-works.htm) or [TauDEM](https://hydrology.usu.edu/taudem/taudem5/help53/D8FlowDirections.html) format.

   * A parameter grid. (i.e. [DAYMET precipitation](https://daac.ornl.gov/cgi-bin/dataset_lister.pl?p=32),
   or [land cover](https://cds.climate.copernicus.eu/cdsapp#!/dataset/satellite-land-cover?tab=overview)).
      * Note that the resolution and coordinate reference system (CRS) do not need to match the FDR.
      However, the data extent should completely overlap the FDR for accurate results.
   * A `.shp` Watershed Boundary Dataset with unique basin IDs. Note that the tools expect HUC12 IDs by default (optional).

## Example 1 - Make a basic precipitation FCPG
Here we use local gridded precipitation data to make a FCPG using the `pysheds` engine. We then save the result locally. Note that all `fcpgtools` outputs are `xarray.DataArray` objects.
```python
import fcpgtools
from pathlib import Path

# get in/out directory paths
# note: replace with your own paths
in_data_dir = Path.cwd() / Path('in_data')
out_data_dir = Path.cwd() / Path('out_data')

# get FDR data path
fdr_tif_path = in_data_dir / Path('validation_upstream_fdr.tif')

# make a flow accumulation raster
flow_accum = fcpgtools.accumulate_flow(
   d8_fdr=fdr_tif_path,
   engine='pysheds',
)

# get precipitation data path
precipitation_tif_path = in_data_dir / Path('validation_daymet_an_P_2017.tif')

# align the parameter grid with the FDR
aligned_precip = fcpgtools.align_raster(
   parameter_raster=precipitation_tif_path,
   d8_fdr=fdr_tif_path,
   resample_method='bilinear',
)

# make a precipitation accumulation raster
precip_accum = fcpgtools.accumulate_parameter(
   d8_fdr=fdr_tif_path,
   parameter_raster=aligned_precip,
   engine='pysheds',
)

# create a FCPG and save locally
out_fcpg_path = out_data_dir / Path('precipitation_fcpg.tif')

precip_fcpg = fcpgtools.make_fcpg(
    param_accum_raster=precip_accum,
    fac_raster=flow_accum,
    out_path=out_fcpg_path,
)

# plot the output (works in a notebook environment)
precip_fcpg.plot()
```

## Example 2 - Cascade accumulated precipitation from one basin to another
Here we **continue from example 1** by cascading accumulated precipitation at the pour point of the upstream basin to the next basin downstream. This can be thought of as updating the boundary conditions of a basins parameter accumulation calculation.

In this example we use a watershed defined at the [HUC4 level](https://nas.er.usgs.gov/hucs.aspx), however, any shapefile can be used to define watershed boundaries as long as a unique identifier is passed into the `basin_id_field` parameter of `find_basin_pour_points()` and `use_huc4=False`.

```python
# pull in HUC12 basin boundaries (will be converted to HUC4 later)
huc12_basins_shp_path = in_data_dir / Path('basin_boundaries.shp')

huc12_basins_shp = fcpgtools.load_shapefile(huc12_basins_shp_path)

# get the HUC4 basin pour point values from our example 1 precipitation accumulation
pour_point_locations_dict = fcpgtools.find_basin_pour_points(
   fac_raster=precip_accum, 
   basins_shp=huc12_basins_shp, 
   basin_id_field='HUC12', 
   use_huc4=True,
)

pour_point_values_dict = fcpgtools.get_pour_point_values(
   pour_points_dict=pour_point_locations_dict, 
   accumulation_raster=precip_accumulation,
)

# get  downstream FDR data path
downstream_fdr_path = in_data_dir / Path('validation_downstream_fdr.tif')

# get upstream and downstream precipitation data paths
# NOTE: this is for explanatory purposes only, downstream basin precipitation data is not stored in this repo!
downstream_precip_data_path = in_data_dir / Path('downstream_daymet_P_2017.tif')

# align the downstream parameter grid with the downstream FDR
aligned_ds_precip = fcpgtools.align_raster(
   parameter_raster=downstream_precip_data_path,
   d8_fdr=downstream_fdr_path,
   resample_method='bilinear',
)

# accumulate downstream accumulation with the cascaded precipitation values
ds_precip_accum = fcpgtools.accumulate_parameter(
   d8_fdr=downstream_fdr_path,
   parameter_raster=aligned_ds_precip,
   engine='pysheds',
   upstream_pour_points=pour_point_locations_dict,
)
```


## Example 3 - Accumulate land cover
Here we use a categorical land cover raster as the parameter grid. Note that the output will be a multi-band `xarray.DataArray` object where each band stores the accumulation of an unique land cover class. Additionally, by using the optional `categories_dict` of `binarize_categorical_raster()` we can add string labels to each output land cover class accumulation band.

```python
# get land use data path
land_use_tif_path = in_data_dir / Path('NALCMS_2015.tif')

# define labels for each land cover class of interest
landcover_classes = {
    1: 'evergreen forest',
    7: 'tropical shrubland',
    8: 'temperate shrubland',
    9: 'tropical grassland',
    10: 'temperate grassland',
    14: 'wetland',
    15: 'cropland',
    16: 'barren',
    17: 'urban',
    18: 'open water',
}

# prepare the categorical raster for accumulation and ignore 'open_water'
land_cover_raster = fcpgtools.(
   cat_raster=land_use_tif_path, 
   categories_dict=landcover_classes, 
   ignore_categories=['open water'], 
)

# align the parameter grid with the FDR
# NOTE: resample_method should == 'nearest' when accumulating categorical rasters!
aligned_land_cover = fcpgtools.align_raster(
   parameter_raster=land_cover_raster,
   d8_fdr=fdr_tif_path,
   resample_method='nearest',
)

# make a land cover accumulation raster
precip_accum = fcpgtools.accumulate_parameter(
   d8_fdr=fdr_tif_path,
   parameter_raster=aligned_land_cover,
   engine='pysheds',
)
```

## Example 4 - Use `TauDEM` to make a decayed accumulation raster
Here we **build off the outputs from example 1** and create a precipitation FCPG accumlation values are "decayed" by their distance from the nearest stream. We then sample the output decayed FCPG at a multiple points. 
   * Her we define "streams" as cells having >= 200 cells upstream. 
   * Also note that this functionality is currently only enabled using `engine='taudem'`.

```python
# create a distance to stream raster
# NOTE: here we also demo how to use taudem kwargs to customize cmd line execution
dist2stream_raster = fcpgtools.distance_to_stream(
   d8_fdr=fdr_tif_path, 
   fac_raster=flow_accum, 
   accum_threshold=200, 
   engine='taudem', 
   kwargs={'cores': 8},
)

# create a decay weighting raster
# NOTE: here we use a medium decay factor of 2
decay_weights = fcpgtools.make_decay_raster(
   distance_to_stream_raster=dist2stream_raster, 
   decay_factor=2,
)

# create a decayed precipitation accumulation raster using the previously "aligned" data
decay_precip_accum = fcpgtools.decay_accumulation(
   d8_fdr=fdr_tif_path, 
   decay_raster=, 
   engine='taudem', 
   parameter_raster=aligned_precip,
   kwargs={'cores': 8},
)

# create path to save output locally
out_decay_fcpg_path = out_data_dir / Path('decay_precipitation_fcpg.tif')

# create a decayed precipitation FCPG
decay_precip_fcpg = fcpgtools.make_fcpg(
   param_accum_raster=decay_precip_accum, 
   fac_raster=flow_accum, 
   out_path=out_decay_fcpg_path,
)

# create a dictionary of type=PourPointLocationsDict to define points of interest
sample_points_dict = {
   pour_point_ids=[
      'gage1', 
      'gage2', 
      'gage3',
   ]
   pour_point_coords=[
      (31.4324, -45.4325), 
      (31.9931, -45.8988), 
      (32.004, -45.1235),
   ]
}

# sample the decay FCPG at our points of interets
sampled_fcpg_dict = fcpgtools.get_pour_point_values(
   pour_points_dict=sample_points_dict, 
   accumulation_raster=decay_precip_fcpg,
)

# note that the output would have the following form for a 6 month/band precipitation raster
print(sampled_fcpg_dict) -> {
   pour_point_ids=[
      'gage1', 
      'gage2', 
      'gage3',
   ]
   pour_point_coords=[
      (31.4324, -45.4325), 
      (31.9931, -45.8988), 
      (32.004, -45.1235),
   ]

   # NOTE: the list position index corresponds to precipitation raster band index
   pour_point_values=[
      [12.3, 13.4, 25.1, 40.1, 20.2, 11.9],
      [7.4, 2.0, 15.6, 15.5, 14.7, 0.8],
      [9.1, 10.4, 15.6, 20.1, 22.4, 0.4],
   ]
}
```






   