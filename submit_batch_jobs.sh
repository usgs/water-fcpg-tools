for reg in {01..18};
do
	inDir=~/projects/CPGtools/data/nlcd_imperv
	tauFDR=~/projects/CPGtools/data/NHDplusV21_facfdr/region_${reg}_fdr_tau.tiff
	tauFAC=region_${reg}_fac.vrt
	workDir=./data/work/${reg}
	outDir=./data/cpg_datasets
	logDir=./logs/${reg}
	cores=20
	accumThresh=110 # similar to 1000 cells with 10 m cells
	overwrite=True

	python batchCPGs.py $inDir $tauFDR $tauFAC $workDir $outDir $logDir $cores $accumThresh $overwrite
done