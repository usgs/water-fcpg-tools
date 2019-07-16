import pandas as pd
import numpy as np
import rasterio as rs
import os
import glob
from collections import Counter

obsFile = "../data/observations/flowPerm_07152019_USGSAlbers_HUC1002.csv"
CPGdir = "../CPGs/1002"
HUC = 1002


data = pd.read_csv(obsFile, encoding = "ISO-8859-1")

data.Date =  pd.to_datetime(data.Date, format='%m/%d/%Y')

#Populate the year, month, and day columns
data.Year = pd.DatetimeIndex(data.Date).year.map("{:04}".format)
data.Month = pd.DatetimeIndex(data.Date).month.map("{:02}".format)
data.Day = pd.DatetimeIndex(data.Date).day.map("{:02}".format)

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


dynamicPaths = data[['FID', 'Lat', 'Long', 'Site_ID', 'Waterbody', 'Date', 'Year', 'Month', 'Day', 'USGS_Albers', 'Source', 'Binary']].copy() #Create dataframe to store file paths to dynamic CPGs


#Dynamic parameter lists



gridMET_PRmmList = ["gridMET_PRmm_Oct", "gridMET_PRmm_Nov", "gridMET_PRmm_Dec", "gridMET_PRmm_Jan", "gridMET_PRmm_Feb", "gridMET_PRmm_Mar", "gridMET_PRmm_Apr", "gridMET_PRmm_May", "gridMET_PRmm_Jun", "gridMET_PRmm_Jul", "gridMET_PRmm_Aug", "gridMET_PRmm_Sep"]
gridMET_minTempKList = ["gridMET_minTempK_Oct", "gridMET_minTempK_Nov", "gridMET_minTempK_Dec", "gridMET_minTempK_Jan", "gridMET_minTempK_Feb", "gridMET_minTempK_Mar", "gridMET_minTempK_Apr", "gridMET_minTempK_May", "gridMET_minTempK_Jun", "gridMET_minTempK_Jul", "gridMET_minTempK_Aug", "gridMET_minTempK_Sep"]
gridMET_SOILMOISTmmList = ["gridMET_SOILMOISTmm_Oct", "gridMET_SOILMOISTmm_Nov", "gridMET_SOILMOISTmm_Dec", "gridMET_SOILMOISTmm_Jan", "gridMET_SOILMOISTmm_Feb", "gridMET_SOILMOISTmm_Mar", "gridMET_SOILMOISTmm_Apr", "gridMET_SOILMOISTmm_May", "gridMET_SOILMOISTmm_Jun", "gridMET_SOILMOISTmm_Jul", "gridMET_SOILMOISTmm_Aug", "gridMET_SOILMOISTmm_Sep"]

SNODAS_SWEmmList = [ "SNODAS_SWEmm_Jan", "SNODAS_SWEmm_Feb", "SNODAS_SWEmm_Mar", "SNODAS_SWEmm_Apr", "SNODAS_SWEmm_May", "SNODAS_SWEmm_Jun", "SNODAS_SWEmm_Jul"]

landsat_NDVIMayOctList = ["landsat_NDVI-May-Oct"]

dynamicPaths = pd.concat([dynamicPaths, pd.DataFrame(columns=gridMET_SOILMOISTmmList), pd.DataFrame(columns=SNODAS_SWEmmList), pd.DataFrame(columns=landsat_NDVIMayOctList), pd.DataFrame(columns=gridMET_minTempKList)], sort=False)

dynamicValues = dynamicPaths.copy()


def SNODAS_SWEmm_fcn(HUC, year, month):

    year = int(year)
    month = int(month)
    day = "01"
    param = "SNODAS_SWEmm"
    CPGdict = {}

    if month >= 10 or month < 3:
        #The month is in the first part of the water year and there is no SWE data to report for the period  
        return CPGdict

    else:
        #SWE data is available
        for m in range(3, min(month + 1,7)):
            monthAbbr = monthList[m -1] #Get month abbreviation from list

            if os.path.isfile(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2), day, HUC))):
                #Only one parameter CPG match the timeframe exists 
                monthCPG = os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2), day, HUC))
            else:
                #A unique CPG file does not exist
                print("Error: no unique CPG exists for parameter {0} in {1} {2}".format(param, str(m).zfill(2), year))
                monthCPG = ""

            CPGdict[monthAbbr] = monthCPG
    
    print(CPGdict)
    return CPGdict



def gridMET_minTempK_fcn(HUC, year, month):

    year = int(year)
    month = int(month)
    day = "??"
    param = "gridMET_minTempK"
    CPGdict = {}

    if month >= 10:
        #Water year only includes data from calendar year
    
        for m in range(10, month +1):

            monthAbbr = monthList[m -1] #Get month abbreviation from list

            if len(glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2) , day, HUC)))) == 1:
                #Only one parameter CPG match the timeframe exists  
                monthCPG = glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2), day, HUC)))[0]
            else:
                #Multipe parameter CPGs match the timeframe exists 
                print("Error: no unique CPG exists for parameter {0} in {1} {2}".format(param, monthAbbr, year))
                monthCPG = ""
                
            CPGdict[monthAbbr] = monthCPG

    else:
        #Water year includes data from two calendar years

        for m in range(10, 13):
            #Handle last months of the last calendar year
            lastyear = year - 1
            monthAbbr = monthList[m -1] #Get month abbreviation from list

            if len(glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, lastyear, str(m).zfill(2), day, HUC)))) == 1:
                #Only one parameter CPG match the timeframe exists  
                monthCPG = glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, lastyear, str(m).zfill(2), day, HUC)))[0]
            else:
                #Multipe parameter CPGs match the timeframe exists 
                print("Error: no unique CPG exists for parameter {0} in {1} {2}".format(param, monthAbbr, lastyear))
                monthCPG = ""

            CPGdict[monthAbbr] = monthCPG

        for m in range(1, month + 1):
            #Handle the current calendar year
            monthAbbr = monthList[m -1] #Get month abbreviation from list

            if len(glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(month).zfill(2), "*", HUC)))) == 1:
                #Only one parameter CPG match the timeframe exists  
                monthCPG = glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(month).zfill(2), "*", HUC)))[0]
            else:
                #Multipe parameter CPGs match the timeframe exists 
                print("Error: multiple CPGs exit for parameter {0} in {1} {2}".format(param, monthAbbr, year))
                monthCPG = ""

            CPGdict[monthAbbr] = monthCPG
    
    print(CPGdict)
    return CPGdict



monthList = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

#dynamicParams = [("SNODAS_SWEmm", SNODAS_SWEmm_fcn), ("gridMET_minTempK", gridMET_minTempK_fcn)]
dynamicParams = [ ("gridMET_minTempK", gridMET_minTempK_fcn)]

for index, row in dynamicPaths.iterrows():

    obsYear = row['Year']
    obsMonth = row['Month']

    
    for paramName,paramF in dynamicParams:

        print(paramName)
        CPGdict = paramF(HUC, obsYear, obsMonth)
        
        for key, value in CPGdict.items():
            
            dynamicPaths.at[index, "{0}_{1}".format(paramName, key)]= value #Add the file path to the data frame

            print("{0}_{1}".format(paramName, key))

            paramCPG = value
            coords = row['USGS_Albers']

            if os.path.isfile(paramCPG):
                with rs.open(paramCPG) as ds:

                    #CPGvalues = ds.sample(list(data['USGS_Albers']),1)
                    CPGvalues = ds.sample([coords],1)
                    try:
                        CPGval = next(CPGvalues)
                        dynamicValues.at[index, "{0}_{1}".format(paramName, key)]= CPGval[0]
                    except:
                        print("Error getting CPG value")
            else:
                print("Error file not found: {0}".format(paramCPG))


dynamicValues.to_csv("../work/1002/obsTest.csv")

print(dynamicPaths)
print(static)
print(dynamic)
print(dynamicValues)


