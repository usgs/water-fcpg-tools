source activate py36

cd ./data/downstream_CPG_test/

# reproject cutline
ogr2ogr -overwrite -t_srs '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs' ./downstream_cpg_test_boundary_proj.shp ./downstream_cpg_test_boundary.shp

# buffer
ogr2ogr -overwrite -dialect sqlite -sql "SELECT ST_BUFFER(Geometry,120), HUC10 FROM downstream_cpg_test_boundary_proj" ./downstream_cpg_test_boundary_proj_buff.shp ./downstream_cpg_test_boundary_proj.shp

for huc in {1402000102,1402000101,1402000201}; do
    gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -tr 30 30 -t_srs '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs' -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ../NHDplusV21_facfdr/region_14_fac.vrt fac_${huc}.tiff

    gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -tr 30 30 -t_srs '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs' -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ../NHDplusV21_facfdr/NHDPlusFdrFac14a/fdr/hdr.adf ./fdr_${huc}.tiff

    gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -tr 30 30 -t_srs '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs' -cutline ./downstream_cpg_test_boundary_proj.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ../NHDplusV21/NHDPlusHydrodem14a/hydrodem/hdr.adf ./hydroDEM_${huc}.tiff

    for fl in `ls -1 ../cpg_datasets/*.tiff`; do
        name=$(basename "$fl") # extract the trailing file name

        gdalwarp -overwrite -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -tr 30 30 -t_srs '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs' -cutline ./downstream_cpg_test_boundary_proj_buff.shp -crop_to_cutline -cwhere "HUC10='${huc}'" ${fl} huc_${huc}_${name}
    done

done