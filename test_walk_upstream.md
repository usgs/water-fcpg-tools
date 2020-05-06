---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.2'
      jupytext_version: 1.4.2
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python
import rasterio as rs
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

from tools import *

from rasterio.mask import mask

from shapely.geometry import LineString, Point
```

```python
with rs.open('./data/longest_flowpath/01080102/str900/hdr.adf') as src:
    st = src.read(1)
```

```python
basins = gpd.read_file('./data/longest_flowpath/test_watersheds.geojson/test_watersheds.shp')
```

```python
data = rs.open('./data/longest_flowpath/01080102/str900/hdr.adf')
```

```python
basins = basins.to_crs(data.crs.to_proj4())
```

```python
row = basins.loc[basins.geometry.area == basins.geometry.area.min()].copy()
row['geometry'] = row.geometry.buffer(50)
coords = getFeatures(row)

out_img, out_transform = mask(data, shapes=coords, crop=True)

st = np.flipud(out_img[0])

st[st == data.nodata] = 0
```

```python
y,x = np.where(st==1)
```

```python
plt.figure(figsize = (15,10))
plt.pcolormesh(st, cmap = 'Blues')
plt.axis('equal')
plt.plot(x[0]+0.5,y[0]+0.5,'r.')
```

```python
out = np.zeros_like(st)

#test N
out[y,x] += st[y+1,x]

# test NE
out[y,x] += st[y+1,x+1]

# test E
out[y,x] += st[y,x+1]

# test SE
out[y,x] += st[y-1,x+1]

# test S
out[y,x] += st[y-1,x]

# test SW
out[y,x] += st[y-1,x-1]

# test W
out[y,x] += st[y,x-1]

# test NW
out[y,x] += st[y+1,x-1]
```

```python
newY, newX = np.where(out == 1)
```

```python
np.where(out == 1)
```

```python
ys = newY[3]
xs = newX[3]
```

```python
plt.pcolormesh(st, cmap = 'Blues')
plt.plot(xs, ys, '.r', label = 'str900 termination')
plt.legend()
```

```python
data = rs.open('./data/longest_flowpath/01080102/fdr/hdr.adf')
out_img, out_transform = mask(data, shapes=coords, crop=True)

fdr = np.flipud(out_img[0])
```

```python
data = rs.open('./data/longest_flowpath/01080102/fac/hdr.adf')
out_img, out_transform = mask(data, shapes=coords, crop=True)

fac = np.flipud(out_img[0])
fac[fac==data.nodata] = 0
```

```python
data = rs.open('./data/longest_flowpath/01080102/dem/hdr.adf')
out_img, out_transform = mask(data, shapes=coords, crop=True)

dem = np.flipud(out_img[0])
```

```python
plt.pcolormesh(fac)
plt.axis('equal')
plt.plot(xs, ys, '.r', label = 'str900 termination')
```

```python
directions = dict()
```

```python
x = 0
y = 0

dirs = ['N','NE','E','SE','S','SW','W','NW']
dirNums = [64,128,1,2,4,8,16,32]
xs = np.array([x,x+1,x+1,x+1,x,x-1,x-1,x-1])
ys = np.array([y+1,y+1,y,y-1,y-1,y-1,y,y+1])

res = np.arctan2(ys-y,xs-x)

directions = {}
for i,v in zip(res,dirNums):
    directions.update({round(i,3):v})
```

```python
res
```

```python
x1 = 5
y1 = 11

x2 = 6
y2 = 11


res = np.arctan2(y2-y1,x2-x1)
print(round(res,3))

plt.plot(x1,y1,'.k')
plt.plot(x2,y2,'.r')
```

```python
directions = {''}
```

```python

```

```python
vals
```

```python

# starting points
ys = newY[3]
xs = newX[3]

# convert row,col to coordinates
h,v = rs.transform.xy(out_transform,ys,xs)

yList = []
xList = []

yList.append(v)
xList.append(h)

# make some plotting vars
rowList = []
colList = []

rowList.append(ys)
colList.append(xs)

newVal = 1
val = dem[ys,xs]
demVal = dem[ys,xs]
idx = -1
i = 0
facVal = 90
while facVal != 0 : # iterate until the cell is surrounded by cells of the same values.
    vals = dem[ys-1:ys+2,xs-1:xs+2].flatten() # take a chunk around the point of interest
    corrVals = vals-val # subtract the original elevation
    vals.sort() # sort dem values
    corrVals.sort() # sort corrected values
    
    
    
    val = newVal # set old newVal to val before resetting newVal
    newVal = vals[np.where(corrVals > 0)[0][idx]]
    print(newVal)

    newYs,newXs = np.where(dem == newVal) # find the next value upstream

    newYs = newYs[(ys-1<=newYs) & (newYs<=ys+2)] # check that the point is within 1 cell of the original point
    newXs = newXs[(xs-1<=newXs) & (newXs<=xs+2)] 

    # don't deal with branches, update the search point to the next cell
    ys = newYs[0]
    xs = newXs[0]

    facVal = fac[ys,xs] # update facVal

    # convert row,col to coordinates
    h,v = rs.transform.xy(out_transform,ys,xs)
    yList.append(v)
    xList.append(h)

    rowList.append(ys)
    colList.append(xs)
    i += 1

    print('Iteration: %s'%i)
    print('\tElev: %s'%newVal)
    print('\told Elev: %s'%val)
    print('\tFAC: %s'%facVal)


```

```python
points = [Point(xy) for xy in zip(xList,yList)]
line = LineString(points)
```

```python
plt.pcolormesh(fac)
plt.axis('equal')
plt.plot(np.array(colList)+0.5, np.array(rowList)+0.5, '.r', label = 'str900 termination')
plt.xlim(20,55)
plt.ylim(130,160)
```

```python
vals
```

```python

vals = np.array((fac[ys+1,xs], # north
                    fac[ys+1,xs+1], # northeast
                    fac[ys,xs+1], # east
                    fac[ys-1,xs+1], # southeast
                    fac[ys-1,xs], # south
                    fac[ys-1,xs-1], # southwest
                    fac[ys,xs-1], # west
                    fac[ys+1,xs-1])) # northwest
```

```python
vals
```

```python

```
