#!/usr/bin/env bash
# $1 - region

r.external in=/home/tbarnhart/projects/DEM_processing/data/NHDplusV21/region_${1}.vrt out=elev --overwrite --quiet -o
g.region rast=elev # reset region 
r.watershed -m elev=elev str=str thresh=500 mem=118000 --overwrite --quiet # generate stream raster map for snapping
