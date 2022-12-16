Getting Started
================
## Installation
`FCPGtools` can be installed from [`PyPI`](TODO:ADD LINK HERE) or [`conda-forge`](TODO:ADD LINK HERE) via the command line.

To install begin by activating your chosen Python >= 3.7 environment, and the running one of the following commands:

```
pip install fcpgtools
```

```
conda install -c conda-forge fcpgtools
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