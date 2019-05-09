from tools import *


inParam = ../100500010101/dem100500010101.tif
fdr = ../100500010101/fdr100500010101.tif
outParam = ../100500010101/rs100500010101.tif
resampleMethod = 1

resampleParam(inParam, fdr, outParam, resampleMethod)