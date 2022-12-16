Cookbook
========

Here we provide a few example work flows for common FCPG tasks.

# Input Data
To produce a basic FCPG you will need the following data for the same geographic area:

   * A Flow Direction Raster (FDR), either in [ESRI](https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/how-flow-direction-works.htm) or [TauDEM](https://hydrology.usu.edu/taudem/taudem5/help53/D8FlowDirections.html) format.

   * A parameter grid. (i.e. [DAYMET precipitation](https://daac.ornl.gov/cgi-bin/dataset_lister.pl?p=32),
   or [land cover](https://cds.climate.copernicus.eu/cdsapp#!/dataset/satellite-land-cover?tab=overview)).
      * Note that the resolution and coordinate reference system (CRS) do not need to match the FDR.
      However, the data extent should completely overlap the FDR for accurate results.
   * A `.shp` Watershed Boundary Dataset with unique basin IDs. Note that the tools expect HUC12 IDs by default (optional).

# Example 1 - Make a basic precipitation FCPG
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
```

# Example 2 - Cascade accumulated precipitation from one basin to another
Here we **continue from example 1** by cascading downslope precipitation accumulation raster (`precip_accum`) from one basin to a another. This can be thought of as updating the boundary conditions of a basins precipitation accumulation.


# Example 3 - Accumulate land cover
Here we use a categorical land cover raster as the parameter grid. Note that the output will be a multi-band `xarray.DataArray` object where each band stores the accumulation of an unique land cover class.

# Example 4 - Use `TauDEM` to make a decayed accumulation raster
Here we create an accumulation raster where values are "decayed" by their distance from the nearest stream. Note that in this example streams are defined as cells having >= 200 upstream cells.






   