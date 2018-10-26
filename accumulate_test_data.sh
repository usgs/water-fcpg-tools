cd ./data/downstream_CPG_test

for huc in {'1402000102','1402000101','1402000201'}; do
	echo $huc
	mpiexec -n 8 aread8 -p fdr_${huc}_tau.tiff -ad8 huc_${huc}_accum.tiff -nc
done
