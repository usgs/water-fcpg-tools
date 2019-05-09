from tools import *
import rasterio as rs

inParam = "../100500010101/2015PRISM_100500010101.tif"
fdr = "../100500010101/fdr100500010101.tif"
outParam = "../100500010101/PRISM100500010101.tif"
resampleMethod = 1

resampleParam(inParam, fdr, outParam, resampleMethod)