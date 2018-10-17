# Script to reprocess NHD hydroDEMs
# Theodore Barnhart
# tbarnhart@usgs.gov

cd /home/tbarnhart/projects/DEM_processing/data/NHDplusV21

for fl in `ls -1 NHDPlusHydrodem???/hydrodem/hdr.*`; do
    tmp="$(cut -d '/' -f1 <<< $fl)" # grab the first part of the file name string
    reg="$(cut -d 'm' -f2 <<< $tmp)" # grab the section after hydrodem

    echo $reg
    gdalwarp -overwrite -tr 30 30 -of GTiff -co "PROFILE=GeoTIFF" -co "TILED=YES" -co "SPARSE_OK=TRUE" -co "COMPRESS=LZW" -co "NUM_THREADS=ALL_CPUS" -t_srs EPSG:42303 -dstnodata -9999 $fl ./reg${reg}.tiff
done