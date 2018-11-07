source activate py36
reg=$1 # pull the region from the command line

cd ./data/gauges

echo Starting $reg
for fl in `ls -1 region_${reg}*.shp`; do

    echo Processing ${fl}
	ogr2ogr -overwrite -a_srs EPSG:42303 ../gauges_proj/${fl} ${fl}

done