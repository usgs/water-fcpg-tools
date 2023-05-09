"""FCPGtools package.

Flow-Conditioned Parameter Grid Tools (FCPGtools) is a Python 3 library that 
enables users to quickly create flow-conditioned parameter grids (FCPGs), 
as well other gridded output datasets, for use in statistical, 
machine learning, and physical hydrologic modeling.

For more information and use examples see our documentation: 
https://usgs.github.io/water-fcpg-tools/build/html/index.html

"""

__version__ = '2.0.4'

from fcpgtools.tools import (
    accumulate_flow,
    accumulate_parameter,
    adjust_parameter_raster,
    align_raster,
    binarize_categorical_raster,
    binarize_nodata,
    check_function_kwargs,
    clip,
    convert_fdr_formats,
    d8_to_dinfinity,
    decay_accumulation,
    distance_to_stream,
    extreme_upslope_values,
    find_basin_pour_points,
    find_fac_pour_point,
    get_pour_point_values,
    load_raster,
    load_shapefile,
    make_decay_raster,
    make_fac_weights,
    make_fcpg,
    mask_streams,
    reproject_raster,
    reproject_shapefile,
    resample,
    save_raster,
    save_shapefile,
    spatial_mask,
    value_mask,
)
__all__ = [
    'accumulate_flow',
    'accumulate_parameter',
    'adjust_parameter_raster',
    'align_raster',
    'binarize_categorical_raster',
    'binarize_nodata',
    'check_function_kwargs',
    'clip',
    'convert_fdr_formats',
    'd8_to_dinfinity',
    'decay_accumulation',
    'distance_to_stream',
    'extreme_upslope_values',
    'find_basin_pour_points',
    'find_fac_pour_point',
    'get_pour_point_values',
    'load_raster',
    'load_shapefile',
    'make_decay_raster',
    'make_fac_weights',
    'make_fcpg',
    'mask_streams',
    'reproject_raster',
    'reproject_shapefile',
    'resample',
    'save_raster',
    'save_shapefile',
    'spatial_mask',
    'value_mask',
]
