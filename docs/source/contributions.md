Contributing Guide
===================

# Where to start?
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

Get started by looking through the list of [open issues](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/issues) to explore bugs or improvments suggested by others. If an open issue resonates, comment on it and ask how you might help.

If you have a new suggestion [open a new issue](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/issues) to share your ideas and begin a discussion about potential solutions. If you are reporting a bug, provide enough detail so others can reproduce the bug.

# Contributing Code or Documentation
Once you have identified or created an issue that you would like to address, use Git to create a feature branch to start modifying any file in the repository, whether it is source code, test code, examples, or documenation.


## Git Best Practices
Thie project follows [GitFlow workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) conventions, in which branches serve these specific purposes:
- `main` branch reflects the latest release
- `develop` branch is a functioning candidate for the next release
- short-lived feature branches are created from `develop` to actively work on an issue.

To contribute, create a feature branch from `develop`, work on your updates, commiting often (at least every couple of hours of work), once your update is working issue a merge request back to the `develop` branch, and ask someone to review your merge request.

## Tools vs Utilities
The main functions of FCPGtools exist in two module files, `tools.py` and `utilities.py`. It is important to understand the different purpose of these modules before contributing.

**`tools.py`** contains functions for the main workflow used by end-users, including all that read/write files.
- Use from `fcpgtools` namespace
- Future edits should always be backward compatible for all v2.x releases, to accept the same inputs and provide the same outputs.

**`utilties.py`** contains functions used by tools.py, most often repeatedly, and also accessible to the user.
- Use from `fcpgtools.utilities` namespace
- Future edits could be allowed to break backward compatibility within v2.x releases, as these are primarily intended to be used internally by functions in tools.py.


## Input file types
To support a new input file type, update either the `custom_types.RasterSuffixes` or `custom_types.ShapefileSuffixes` tuple with the relevant file suffix (i.e., `.nc`). Then add an `elif` statement under `tools.load_raster()` or `tools.load_shapefile()` to handle the new extension type. Similarly, to support saving to new file type, add an `elif` statement to `tools.save_raster()` or `tools.save_shapefile()`.

## Terrain Engines
Adding a new `terrain_engine` or expanding a `terrain_engine`'s functionality requires an understanding of a specific object oriented structural subtyping capability introduced with Python 3.8.

The TerrainEngine geospatial methods are specified as [Python Protocols](https://peps.python.org/pep-0544/) in the `terrain_engine/protocols.py`. These Protocols define the abstract signature of the various geospatial methods to be implemented in separate classes using python geospatial libraries to perform the necessary geospatial operations.

To add additional TerrainEngines the developer should define a new class and implement the protocols (or a subset) defined in terrain_engine/protocols.py.

To add additional geospatial functions the developer should first define a new protocol in the terrain_engine/protocols.py file. That protocol will define the abstract signature of the new geospatial method (including function name, arguments, and return type). Once a protocol is defined, a concrete implementation of the protocol can be developed in any of the various TerrainEngines.

Note a future refactoring should consider leverage a plugin architecture for easier integration of third party TerrainEngines.


## Adding a new D8 Flow Direction Raster (FDR) format
To support a new D8 Flow Direction Raster (FDR) format, simply add a key-value mapping in `custom_types.D8ConversionDicts` where the key is the new formats name **in lower case**, and the value is a dictionary mapping each cardinal direction + nodata to an integer value.

# Issuing a release (PyPi maintainers only)
1. Start with a fresh `fcgptools_base` environment by cloning our [`environment.yml`](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/blob/master/environment.yml) file.
2. Search the entire directory to find references to the version number, and increment appropriately.
3. Make a merge-request on GitLab to merge your feature or develop branch into the master branch. Once successful, switch to the master branch.
4. Using the `conda` terminal, navigate to `/FCPGtools` containing the `pyproject.toml` and `poetry.lock` files.
5. Run the following commands in sequence to resolve the environment dependencies, install the updated copy of `fcpgtools` into your environment, then build a local wheel file for distribution:
    ```
    poetry lock
    poetry install
    poetry build
    ```
    * NOTE: The reason we use `poetry install` last is to make sure there are no issues installing the packaged wheel into our recommended virtual environment.
6. Use `poetry publish -u {YOUR-PyPI-USERNAME} -p {YOUR-PyPI-PASSWORD}` to publish the package to our [`PyPI` distribution](https://pypi.org/project/fcpgtools/).
7. Issue a new release on the GitLab repository ["releases" page](https://code.usgs.gov/StreamStats/data-preparation/cpg/FCPGtools/-/releases). Inform the users of all relevant updates, change to dependencies, and motivation behind the latest release.