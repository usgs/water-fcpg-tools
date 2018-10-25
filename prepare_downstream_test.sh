source activate py36

cd ./data/downstream_CPG_test/

# reproject cutline
ogr2ogr -overwrite -t_srs EPSG:42303 ./downstream_cpg_test_boundary_proj.shp ./downstream_cpg_test_boundary.shp

# buffer
ogr2ogr -overwrite -dialect sqlite -sql "SELECT ST_BUFFER(Geometry,120), HUC10 FROM downstream_cpg_test_boundary_proj" ./downstream_cpg_test_boundary_proj_buff.shp ./downstream_cpg_test_boundary_proj.shp

for huc in {1402000102,1402000101,1402000201}; do
    gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -t_srs EPSG:42303 -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ../NHDplusV21_facfdr/region_14_fac.vrt fac_${huc}.tiff

    gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -t_srs EPSG:42303 -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ../NHDplusV21_facfdr/region_14_fdr_tau.tiff ./fdr_${huc}_tau.tiff

    for fl in `ls -1 ../cpg_datasets/*.tiff`; do
        name=$(basename "$fl") # extract the trailing file name

        gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -t_srs EPSG:42303 -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ${fl} huc_${huc}_${name}
    done

done