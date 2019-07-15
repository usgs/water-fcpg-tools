import pandas as pd
import numpy as np
import rasterio as rs
import os
from collections import Counter

obsFile = "../data/observations/flowPerm_07152019.txt"
CPGdir = "../CPGs/1002"
HUC = 1002


data = pd.read_csv(obsFile)

data.Date =  pd.to_datetime(data.Date, format='%m/%d/%Y %H:%M:%S')

#Populate the year, month, and day columns
data.Year = str(pd.DatetimeIndex(data.Date).year)
data.Month = pd.DatetimeIndex(data.Date).month
data.Day = pd.DatetimeIndex(data.Date).day

#Create column with tuple of point coordinates
data['USGS_Albers'] = list(zip(data.POINTX, data.POINTY))




CPGs = [] #Initialize list of CPGs


if os.path.isdir(CPGdir):
    #Get all covariate files in directory
    for path, subdirs, files in os.walk(CPGdir):
        for name in files:
            #Check if file is .tif, and if so add it to covariate list
            if os.path.splitext(name)[1] == ".tif":
                    CPGs.append(os.path.join(path, name))
else:
    print("Invalid CPG directory")

#Get unique CPG parameters

def getCPGname(CPG):
    basename = os.path.splitext(os.path.basename(CPG))[0] #Get name of CPG file without extention
    paramname = basename.split("_")[0] + "_" + basename.split("_")[1] #Get name of CPG parameter
    return paramname

paramNames = list(map(getCPGname, CPGs))

paramNum = Counter(paramNames) #Counter number of times each parameter name occurs

#Create empty sets for dynamic and static parameter lists
dynamic = set()
static = set()

for param in set(paramNames):
    if paramNum[param] > 1:
        dynamic.add(param)
    else:
        static.add(param)
 
#Sort the parameter paramNames
dynamic = list(dynamic)
static = list(static)
dynamic.sort()
static.sort()

data = pd.concat([data, pd.DataFrame(columns=dynamic), pd.DataFrame(columns=static)], sort=False)

print(data)

#Get static CPG values

for param in static:

    paramCPG = os.path.join(CPGdir, "{0}_HUC{1}_CPG.tif".format(param, HUC)) #Build path to CPG file
    print(paramCPG)
    with rs.open(paramCPG) as ds:
        #CPGvalues = ds.sample(list(data['USGS_Albers']),1)
        CPGvalues = ds.sample([(-124542,44226)],1)



for index, row in data.iterrows():

    obsYear = row['Year']
    obsMonth = row['Month']
    obsDay = 00

    
    for param in dynamic:

        paramCPG = os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, obsYear, obsMonth, obsDay, HUC)) #Build path to CPG file
        print(paramCPG)
        
        with rs.open(paramCPG) as ds:
            #CPGvalues = ds.sample(list(data['USGS_Albers']),1)
            CPGvalues = ds.sample([(-124542,44226)],1)





print(static)
print(dynamic)
print(data)

