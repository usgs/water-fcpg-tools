from tools import *
import rasterio as rs

inParam = "../1005/2015PRISM_Milk.tif"
fdr = "../100500010101/fdr100500010101.tif"
outParam = "../100500010101/PRISM100500010101.tif"
resampleMethod = 1

resampleParam(inParam, fdr, outParam, resampleMethod)