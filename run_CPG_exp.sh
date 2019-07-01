cov=./data/CHI_poster/daymet/daymet_v3_prcp_annttl_2017_na.tif
taufdr=./data/CHI_poster/nhd/fdr_reclass.tif
taufac=./data/CHI_poster/HRNHDPlusRasters1003/fac.tif
workDir=./data/CHI_poster/cpg
outDir=./data/CHI_poster/cpg
cores=6
accumThresh=1000
overwrite=True
deleteTemp=False
huc=1003
python -u ./makeCPG.py $cov $taufdr $taufac $workDir $outDir $cores $accumThresh $overwrite $deleteTemp $huc