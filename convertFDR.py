from tools import tauDrainDir

for reg in range(1,19):
	infl = "./data/NHDplusV21_facfdr/region_%s_fdr_arc.tif"%(str(reg).zfill(2))
	outfl = "./data/NHDplusV21_facfdr/region_%s_fdr_tau.tif"%(str(reg).zfill(2))

	tauDrainDir(infl,outfl)

