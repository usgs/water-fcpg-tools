Contribution Guide
===================

## GitFlow Best Practices

## `tools.py` vs `utilities.py`

## Contribution guide by category
### Supporting additional file types
To support a new input file type, update either the `custom_types.RasterSuffixes` or `custom_types.ShapefileSuffixes` tuple with the relevant file suffix (i.e., `.nc`). Then add an `elif` statement under `tools.load_raster()` or `tools.load_shapefile()` to handle the new extension type. Similarly, to support saving to new file type, add an `elif` statement to `tools.save_raster()` or `tools.save_shapefile()`.

### Supporting more functions with an existing `terrain_engine`
Our `terrain_engine` implementation is based on `terrain_engine/protocols.py` which stores a class that inherits from `typing.Protocol` and contains an [abstract base method](https://docs.python.org/3/library/abc.html) that raises a `NotImplementedError`. This class (i.e. `SupportsAccumulateFlow`) must have the `@runtime_checkable` decorator. The abstract base method defines the arguments, their data types, and the data type of the output using type hints.

### Adding a new `terrain_engine`

### Adding a new D8 Flow Direction Raster (FDR) format
To support a new D8 Flow Direction Raster (FDR) format, simply add a key-value mapping in `custom_types.D8ConversionDicts` where the key is the new formats name **in lower case**, and the value is a dictionary mapping each cardinal direction + nodata to an integer value.

## Issuing a release (PyPi maintainers only)
1. Start with a fresh `fcgptools_base` environment by cloning our [`environment.yml`](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/environment.yml) file.
2. Search the entire directory to find references to the version number, and increment appropriately.
3. Make a merge-request on GitLab to merge your feature or develop branch into the master branch. Once successful, switch to the master branch.
4. Using the `conda` terminal, navigate to `/FCPGtools` containing the `pyproject.toml` and `poetry.lock` files.
5. Run the following commands in sequence to resolve the environment dependencies, build a local wheel file including whatever updates to `fcpgtools` were added, and then install the updated copy of `fcpgtools` into your environment:
    ```
    poetry lock
    poetry build
    poetry install
    ```
    * NOTE: The reason we use `poetry install` last is to make sure there are no issues installing the packaged wheel into our recommended virtual environment.
6. Use `poetry publish -u {YOUR-PyPI-USERNAME} -p {YOUR-PyPI-PASSWORD}` to publish the package to our [`PyPI` distribution](https://pypi.org/project/fcpgtools/).
7. Issue a new release on the GitLab repository ["releases" page](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/releases). Inform the users of all relevant updates, change to dependencies, and motivation behind the latest release.