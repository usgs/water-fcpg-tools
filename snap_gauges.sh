#!/usr/bin/env bash
# $1 - region
# $2 - snap distance in pixels 
# $3 - accumulation area in pixels

reg=$1
dist=$2
thresh=$3

r.in.gdal in=/home/tbarnhart/projects/DEM_processing/data/NHDplusV21_facfdr/region_${reg}_fac.vrt out=accum --overwrite -o --quiet

g.region rast=accum

v.in.ascii -t in=/home/tbarnhart/projects/DEM_processing/data/CATCHMENT_region_${reg}.csv out=gauges x=2 y=3 cat=1 sep=comma format=point skip=1 --overwrite --quiet # import ascii data, don't make table

r.stream.snap in=gauges out=gauges_snap stream=str accumulation=accum threshold=${thresh} radius=${dist} mem=118000 --overwrite --quiet # snap all gauges to stream network

v.out.ogr in=gauges_snap type=point out=./data/CATCHMENT_gauges/CATCUMENT_region_${reg}.shp format=ESRI_Shapefile --overwrite --quiet 

r.out.gdal in=str out=./data/reg${reg}_str.tiff --overwrite createopt="SPARSE_OK=TRUE,COMPRESS=LZW,TILED=YES,PROFILE=GeoTIFF"
