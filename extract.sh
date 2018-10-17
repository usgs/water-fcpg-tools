#!/bin/bash

# inputs
#
# 1 - coarseRes
# 2 - Res
# 3 - buffDist
# 4 - outfl
# 5 - x coord
# 6 - y coord

coarseRes=$1
Res=$2
buffDist=$3
outfl=$4
x=$5
y=$6
reg=$7

g.region rast=elev
g.region res=$coarseRes -a

#echo $5,$6 > ./data/reg${reg}_pour_pt.txt

r.water.outlet in=dir_coarse out=watershed coord=${x},${y} --overwrite --quiet

r.buffer in=watershed out=watershed_buff dist=$buffDist --overwrite --quiet

r.to.vect in=watershed_buff out=boundary_buff type=area --overwrite --quiet

# reset region boundary
g.region vect=boundary_buff
g.region res=$Res -a

# bring in basin pour point
#v.in.ascii in=./data/reg${reg}_pour_pt.txt out=pp format=point sep=comma --overwrite --quiet

#r.snap.outlet in=pp out=ppSnap accum=accum radius=2 thresh=500 # snap pour point to accumulation grid

#v.out.ascii in=ppSnap out=./data/reg${reg}_pour_pt_snap.txt format=point sep=comma --overwrite --quiet

# read the snapped point from the text file
#while IFS=, read -r x y z
#do
r.water.outlet in=dir out=watershed coord=${x},${y} --overwrite --quiet
#done < ./data/reg{reg}_pour_pt_snap.txt

r.to.vect in=watershed out=boundary type=area --overwrite --quiet

v.db.addcolumn map=boundary columns='area_sqkm double precision' --quiet

v.to.db map=boundary option=area columns=area_sqkm units=kilometers --quiet

v.out.ogr in=boundary type=area out=$outfl --overwrite --quiet format=ESRI_Shapefile