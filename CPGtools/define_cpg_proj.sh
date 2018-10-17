

#source activate py36 # define work environment
reg=$1 # pull the region 

srs_def='EPSG:42303'

for fl in `ls -1 ./data/cpg_datasets/output_cpg/*${reg}_cpg.tiff`; do
    echo Processing ${fl}
    gdal_edit.py -a_srs ${srs_def} ${fl}
done