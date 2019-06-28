cov=~/projects/CPGtools/data/CHI_poster/daymet/daymet_v3_prcp_annttl_2017_na.tif
taufdr=~/projects/CPGtools/data/CHI_poster/HRNHDPlusRasters1003/fdr_reclass.tif
taufac=~/projects/CPGtools/data/CHI_poster/HRNHDPlusRasters1003/fac.tif
workDir=~/projects/CPGtools/data/CHI_poster/cpg
outDir=~/projects/CPGtools/data/CHI_poster/cpg
cores=6
accumThresh=1000
overwrite=True
deleteTemp=False
huc=1003
python -u ./makeCPG.py $cov $taufdr $taufac $workDir $outDir $cores $accumThresh $overwrite $deleteTemp $huc