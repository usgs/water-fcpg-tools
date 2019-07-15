import pandas as pd
import numpy as np
import os

obsFile = "../data/observations/flowPerm_07152019.txt"

CPGdir = "../CPGs/1002"

data = pd.read_csv(obsFile)

data.Date =  pd.to_datetime(data.Date, format='%m/%d/%Y %H:%M:%S')

#Populate the year, month, and day columns
data.Year = pd.DatetimeIndex(data.Date).year
data.Month = pd.DatetimeIndex(data.Date).month
data.Day = pd.DatetimeIndex(data.Date).day


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


print(CPGs)
print(data)