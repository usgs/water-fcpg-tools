Flow-Conditioned Parameter Grid (FCPG) Tools Documentation
===============================================================


**For detailed documentation please reference our [ReadTheDocs site](https://usgs.github.io/water-fcpg-tools/)!** 

Please log any issues or feature requests using [this form](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/issues/new?issuable_template=bug).

# Getting Started
## Installation
`FCPGtools` can be installed from [`PyPI`](https://pypi.org/project/fcpgtools/) into a virtual environment containing [`GDAL`](https://anaconda.org/conda-forge/gdal), and for full functionality, [`TauDEM`](https://anaconda.org/conda-forge/taudem) as well.

**We strongly encourage the following installation workflow:**

1. Install the Anaconda Python Distribution or Miniconda
    * [Anaconda Individual Edition](https://www.anaconda.com/products/distribution) - includes `conda`, a complete Python (and R) data science stack, and the helpful Anaconda Navigator GUI.
    * A lighter-weight alternative is to [install Miniconda](https://docs.conda.io/en/latest/miniconda.html).
2. Use the `conda` command line to clone our lightweight `fcpgtools_base` virtual environment that contains non-Python dependencies from the [`environment.yml`](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/environment.yml) file available in our repo. Either clone the repo, or just download the .yml file locally, and run the following commands:

    ```
    conda env create -f {PATH}/environment.yml
    ```
    * **Note:** We also provide a more robust [`environment_dev.yml`](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/environment_dev.yml) virtual environment for developers containing all libraries relevant to making contributions as well as running our [example notebooks](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/examples).
3. Activate the `fcpgtools_base` environment, and pip install `fcpgtools`.
    ```
    pip install fcpgtools
    ```



## Using FCPGtools
Version 2.0 of `FCPGtools` has a "flat" architecture, meaning all functions can be accessed by importing the main `fcpgtools` module as shown in a simple example below:

```python
# creating an flow accumulation raster from a Flow Direction Raster (FDR)
import fcpgtools

path_to_fdr = r'YOUR/PATH/HERE/fdr.tif'

flow_accumulation_grid = fcpgtools.accumulate_flow(
    d8_fdr=path_to_fdr,
) -> xarray.DataArray
```

Please refer to our documentation's [Cookbook](https://usgs.github.io/water-fcpg-tools/cookbook.html) page for more intricate examples of usage.

# Citation
* **Version 2.0** was released in January, 2023.
    * Barnhart, T.B., Nogueira, X.R., Siefken, S.A., Schultz, A.R., Aufenkampe, A., Tomasula, P., 2023, Flow-Conditioned Parameter Grid Tools Version 2.0.
* **Version 1.1** was released in September, 2022.
* **Version 1.0** (IP-112996) was approved on September 3, 2020.
    * Barnhart, T.B., Sando, R., Siefken, S.A., McCarthy, P.M., and Rea, A.H., 2020, Flow-Conditioned Parameter Grid Tools: U.S. Geological Survey Software Release, DOI: https://doi.org/10.5066/P9W8UZ47.

# Migrating from Version 1.0
Version 2.0 of `FCPGtools` is a ground-up refactor and rebuild of Version 1.0. Backwards compatibility is broken, and many work-flows have been significantly streamlined. We strongly suggest that any users accustomed to Version 1.0 reference our [updated documentation site](https://usgs.github.io/water-fcpg-tools/index.html).

**A non-exhaustive list of key updates is below:**
* All functions output an in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object, allowing for functions to be strung together into performance oriented pipelines.
    * [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects have a variety of powerful features and optimizations. For more information please reference the library's [documentation](https://docs.xarray.dev/en/stable/getting-started-guide/why-xarray.html).
    * Rasters can still be saved to a local GeoTIFF file by providing a valid `.tif` path to `param:out_path`.
* All functions can now accept either local string paths, local [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) objects, or in-memory [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) objects.
* Multi-band parameter grids are now supported!
    * Example: Passing a 12-month precipitation raster (where each month is a raster band) into [`fcpgtools.accumulate_parameter()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_parameter) will output a 12-band [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html#xarray.DataArray) object.
* Flow Direction Raster format conversion (i.e. ESRI -> TauDEM) is now automated behind-the-scenes.
* Support for multiple "terrain engines" gives users optionality and increases dependency deprecation resiliancy. 
    * Where necessary users can set `param:engine` to [`taudem`](https://hydrology.usu.edu/taudem/taudem5/) (default) or [`pysheds`](https://github.com/mdbartos/pysheds).
    * Note that the `pysheds` terrain engine is signifcantly more performant, however it currently only supports [`accumulate_flow()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_flow) and [`accumulate_parameter()`](https://usgs.github.io/water-fcpg-tools/functions.html#fcpgtools.tools.accumulate_parameter).

**Please reference our markdown [`refactored_names`](examples/refactored_names.md) document for a complete mapping of Version 1.1 to Version 2.0 function names.**


## Disclaimers
Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.

Please see [DISCLAIMER.md](DISCLAIMER.md) in the project repository.

## License
Please see [LICENSE.md](LICENSE.md) in the project repository.
