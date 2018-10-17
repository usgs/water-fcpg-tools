#!/usr/bin/env bash
# $1 - region
# $2 - snap distance in pixels

v.in.ascii -t in=/home/tbarnhart/projects/DEM_processing/data/CATCHMENT_region_${1}.csv out=gauges x=2 y=3 cat=1 sep=comma format=point skip=1 --overwrite --quiet # import ascii data, don't make table

r.stream.snap in=gauges out=gauges_snap stream=str radius=$2 mem=118000 --overwrite --quiet # snap all gauges to stream network

v.out.ogr in=gauges_snap type=point out=./data/CATCHMENT_gauges/CATCUMENT_region_${1}.shp format=ESRI_Shapefile --overwrite --quiet 

