# import base dependencies
import xarray as xr
import geopandas as gpd
import pydaymet
from pathlib import Path
import os

# import pydaymet to test multi-dimensional report
try:
    import pydaymet
    MULTI_DIMENSIONAL_TEST = True
except ImportError as e:
    print(f'WARNING: Please install pydaymet to test multi-dimensional support.')
    MULTI_DIMENSIONAL_TEST = False

# import fcpgtools!
import fcpgtools


def main(
    multi_dimensional_test: bool = MULTI_DIMENSIONAL_TEST,
    test_pysheds: bool = True,
    test_taudem: bool = True,
    test_pour_points: bool = True,
) -> bool:

    # get all necessary paths for in/out data
    examples_dir = str(Path.cwd())
    if 'FCPGtools' in examples_dir:
        examples_dir = Path(examples_dir.split('FCPGtools', 2)[
                            0]) / Path('FCPGtools/examples')
        print(f'var:examples_dir = {examples_dir}')
    else:
        del examples_dir
        print('ERROR: Cant find /FCPGtools/examples!')

    # get all necessary paths for in/out data
    in_data_dir = examples_dir / Path('in_data')
    print(f'Variable in_data_dir accesses {in_data_dir}')
    out_data_dir = examples_dir / Path('out_data')
    print(f'Variable in_data_dir accesses {out_data_dir}')

    # get tif data paths
    us_fdr_tif = in_data_dir / Path('validation_upstream_fdr.tif')
    ds_fdr_tif = in_data_dir / Path('validation_downstream_fdr.tif')
    landcover_tif = in_data_dir / Path('NALCMS_2015.tif')

    # get upstream basin shapefile path
    us_basin_shp_path = in_data_dir / Path('upstream_wbd.shp')

    # pull data into DataArrays and GeoPandas
    us_fdr = fcpgtools.load_raster(us_fdr_tif)
    landcover = fcpgtools.load_raster(landcover_tif)
    us_basin_shp = gpd.read_file(us_basin_shp_path)

    # pull in precipitation data
    if multi_dimensional_test:
        print('Pulling in multi-dimensional DAYMET precipitation data')
        bounding_box = list(us_basin_shp.geometry.total_bounds)
        print(f'Boudning box: {bounding_box}')

        precip = pydaymet.get_bygeom(
            bounding_box,
            crs=us_basin_shp.crs.to_wkt(),
            dates=("2021-01-01", "2021-12-30"),
            variables='prcp',
            time_scale="monthly",
        )['prcp']
    else:
        print('Using one dimensional precipitation data')
        precip_tif = Path(os.path.join(
            in_data_dir, 'validation_daymet_an_P_2017.tif'))
        precip = fcpgtools.load_raster(precip_tif)
    print('Done\n')

    # align precipitation raster
    print('Aligning precipitation raster to the upstream fdr')
    us_precip = fcpgtools.align_raster(
        precip,
        us_fdr,
        resample_method='bilinear',
        out_path=Path(os.path.join(out_data_dir, 'us_fdr_daymet.tif')),
    )
    print('Done\n')

    # binarize and align landcover raster
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

    print('Aligning landcover raster to the upstream fdr')
    us_landcover = fcpgtools.align_raster(
        landcover,
        us_fdr,
        resample_method='nearest',
        out_path=None
    )

    us_binary_landcover = fcpgtools.binarize_categorical_raster(
        us_landcover,
        categories_dict=landcover_classes,
        ignore_categories=[18]  # ignoring open water
    )
    print('Done\n')

    test_update_dict = {
        'pour_point_ids': ['1407'],
        'pour_point_coords': [(-1370609.9999999995, 1648259.9999999963)],
        'pour_point_values': [[999999]],
    }

    # use the pysheds engine
    if test_pysheds:

        print('PySheds: Making a FAC from us_fdr')
        fac_pysheds = fcpgtools.accumulate_flow(
            us_fdr,
            engine='pysheds',
            upstream_pour_points=None,
            out_path=None,
        )
        print('Done\n')

        if test_pour_points:
            print(
                'Testing getting pour points from pysheds accumulation (HUC12 and HUC4 levels)')
            huc4_pour_points = fcpgtools.find_basin_pour_points(
                fac_pysheds,
                us_basin_shp,
                basin_id_field='HUC12',
                use_huc4=True,
            )

            huc12_pour_points = fcpgtools.find_basin_pour_points(
                fac_pysheds,
                us_basin_shp,
                basin_id_field='HUC12',
                use_huc4=False,
            )

            huc4_pp_values = fcpgtools.get_pour_point_values(
                huc4_pour_points,
                fac_pysheds,
            )

            huc12_pp_values = fcpgtools.get_pour_point_values(
                huc12_pour_points,
                fac_pysheds,
            )

        print('PySheds: Making a daymet accumulation grid')
        daymet_acc_pysheds = fcpgtools.accumulate_parameter(
            us_fdr,
            us_precip,
            engine='pysheds',
            out_path=Path(out_data_dir / Path('test_accum1.tif')),
        )
        print('Done\n')

        print('PySheds: Making a landcover accumulation grid')
        landcover_acc_pysheds = fcpgtools.accumulate_parameter(
            us_fdr,
            us_binary_landcover,
            engine='pysheds',
            out_path=Path(out_data_dir / Path('test_accum2.tif')),
        )
        print('Done\n')

    if test_taudem:

        print('TauDEM: Making a FAC from us_fdr')
        fac_taudem = fcpgtools.accumulate_flow(
            d8_fdr=us_fdr,
            engine='taudem',
            upstream_pour_points=None,
            out_path=Path(Path.cwd() / 'fac.tif'),
            kwargs={'cores': 4},
        )
        print('Done\n')

        if test_pour_points:
            print(
                'Testing getting pour points from TauDEM accumulation (HUC12 and HUC4 levels)')
            huc4_pour_points = fcpgtools.find_basin_pour_points(
                fac_taudem,
                us_basin_shp,
                basin_id_field='HUC12',
                use_huc4=True,
            )

            huc12_pour_points = fcpgtools.find_basin_pour_points(
                fac_taudem,
                us_basin_shp,
                basin_id_field='HUC12',
                use_huc4=False,
            )
            huc4_pp_values = fcpgtools.get_pour_point_values(
                huc4_pour_points,
                fac_taudem,
            )

            huc12_pp_values = fcpgtools.get_pour_point_values(
                huc12_pour_points,
                fac_taudem,
            )
            print('Done\n')

        print('TauDEM: Making a daymet accumulation grid')
        daymet_acc_taudem = fcpgtools.accumulate_parameter(
            us_fdr,
            us_precip,
            engine='taudem',
            kwargs={'cores': 4},
        )
        print('Done\n')
        print('TauDEM: Making a landcover accumulation grid')
        landcover_acc_taudem = fcpgtools.accumulate_parameter(
            us_fdr,
            us_binary_landcover,
            engine='taudem',
            kwargs={'cores': 4},
        )
        print('Done\n')

        print('TauDEM: Making a distance to stream raster')
        distance_to_stream_taudem = fcpgtools.distance_to_stream(
            us_fdr,
            fac_taudem,
            engine='taudem',
            accum_threshold=100,
            out_path=Path(Path.cwd() / 'distance_to_stream.tif')
        )
        print('Done\n')

        print('Making a stream mask w/ 100 as the threshold')
        mask_streams = fcpgtools.mask_streams(
            fac_taudem,
            accumulation_threshold=100,
            out_path=Path(Path.cwd() / 'streammask.tif')
        )
        print('Done\n')

        print('TauDEM: Calculating extream upslope parameter values')
        fcpgtools.extreme_upslope_values(
            us_fdr,
            us_precip,
            engine='taudem',
            mask_streams=None,
            get_min_upslope=False,
            out_path=Path(Path.cwd() / 'max_upslope.tif')
        )
        print('Done\n')

        print('TauDEM: Making decay grid using distance2stream raster')
        decay_raster = fcpgtools.make_decay_raster(
            distance_to_stream_taudem,
            decay_factor=2,
            out_path=Path(Path.cwd() / 'decay.tif'),
        )
        print('Done\n')

        print('TauDEM: Making a precipitation decay accumulation raster')
        fcpgtools.decay_accumulation(
            us_fdr,
            decay_raster,
            engine='taudem',
            upstream_pour_points=None,
            parameter_raster=us_precip,
            out_path=Path(Path.cwd() / 'decay_accumulation.tif'),
        )


if __name__ == '__main__':
    main(
        True,
        test_taudem=True,
        test_pysheds=False,
        test_pour_points=False,
    )
