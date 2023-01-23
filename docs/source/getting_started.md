Getting Started
================
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
4. (optional) pip install optional libraries required to run our demo notebook ([`examples/v2_fcpgtools_demo.ipynb`](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/examples/v2_fcpgtools_demo.ipynb)), and to leverage in-line function completion/type-hints.
    ```
    pip install jupyterlab
    pip install ipympl
    pip install python-lsp-server
    pip install jupyterlab-lsp
    pip install pydaymet
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

Note that is you are accustomed to Version 1.0 of `FCPGtools`, you may want to 
start by referencing our 
[Migrating to `FCPGtools` Version 2.0](https://usgs.github.io/water-fcpg-tools/migrating_from_v1.html) 
page.
