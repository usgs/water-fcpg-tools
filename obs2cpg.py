import pandas as pd
import numpy as np
import rasterio as rs
import os
import glob
import calendar
from collections import Counter


#Inputs
obsFile = "../data/observations/flowPerm_07152019_USGSAlbers_HUC1002.csv"
CPGdir = "../CPGs/1002"
HUC = 1002



""" BEGIN PARAMTER FUNCTIONS """

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
        for m in range(3, min(month + 1,8)):
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
    #day = calendar.monthrange(year,month)[1] #Get last date of last day of month
    day = "00"
    param = "gridMET_minTempK"
    CPGdict = {}

    #Water year includes data from two calendar years

    for m in range(month + 1, 13):
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

        if len(glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2), "*", HUC)))) == 1:
            #Only one parameter CPG match the timeframe exists  
            monthCPG = glob.glob(os.path.join(CPGdir, "{0}_{1}_{2}_{3}_HUC{4}_CPG.tif".format(param, year, str(m).zfill(2), "*", HUC)))[0]
        else:
            #Multipe parameter CPGs match the timeframe exists 
            print("Error: no unique CPG exists for parameter {0} in {1} {2}".format(param, monthAbbr, year))
            monthCPG = ""

        CPGdict[monthAbbr] = monthCPG
    
    print(CPGdict)
    return CPGdict



""" END PARAMETER FUNCTIONS """








#Load observations file to dataframe
data = pd.read_csv(obsFile, encoding = "ISO-8859-1")

#Convert date to pandas datetime
data.Date =  pd.to_datetime(data.Date, format='%m/%d/%Y')

#Populate the year, month, and day columns
data.Year = pd.DatetimeIndex(data.Date).year.map("{:04}".format)
data.Month = pd.DatetimeIndex(data.Date).month.map("{:02}".format)
data.Day = pd.DatetimeIndex(data.Date).day.map("{:02}".format)

#Create column with tuple of point coordinates
data['USGS_Albers'] = list(zip(data.POINTX, data.POINTY))


#Get lists of static and dynamic CPGs

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


#Prepare intermediate data frames
staticValues = pd.concat([data, pd.DataFrame(columns=static)], sort=False)


#Dynamic parameter lists
#gridMET_PRmmList = ["gridMET_PRmm_Oct", "gridMET_PRmm_Nov", "gridMET_PRmm_Dec", "gridMET_PRmm_Jan", "gridMET_PRmm_Feb", "gridMET_PRmm_Mar", "gridMET_PRmm_Apr", "gridMET_PRmm_May", "gridMET_PRmm_Jun", "gridMET_PRmm_Jul", "gridMET_PRmm_Aug", "gridMET_PRmm_Sep"]
gridMET_minTempKList = ["gridMET_minTempK_Oct", "gridMET_minTempK_Nov", "gridMET_minTempK_Dec", "gridMET_minTempK_Jan", "gridMET_minTempK_Feb", "gridMET_minTempK_Mar", "gridMET_minTempK_Apr", "gridMET_minTempK_May", "gridMET_minTempK_Jun", "gridMET_minTempK_Jul", "gridMET_minTempK_Aug", "gridMET_minTempK_Sep"]
#gridMET_SOILMOISTmmList = ["gridMET_SOILMOISTmm_Oct", "gridMET_SOILMOISTmm_Nov", "gridMET_SOILMOISTmm_Dec", "gridMET_SOILMOISTmm_Jan", "gridMET_SOILMOISTmm_Feb", "gridMET_SOILMOISTmm_Mar", "gridMET_SOILMOISTmm_Apr", "gridMET_SOILMOISTmm_May", "gridMET_SOILMOISTmm_Jun", "gridMET_SOILMOISTmm_Jul", "gridMET_SOILMOISTmm_Aug", "gridMET_SOILMOISTmm_Sep"]

SNODAS_SWEmmList = [ "SNODAS_SWEmm_Mar", "SNODAS_SWEmm_Apr", "SNODAS_SWEmm_May", "SNODAS_SWEmm_Jun", "SNODAS_SWEmm_Jul"]

landsat_NDVIMayOctList = ["landsat_NDVI-May-Oct"]

dynamicList = gridMET_minTempKList + SNODAS_SWEmmList + landsat_NDVIMayOctList #Combine lists of dynamic parameters

dynamicPaths = pd.concat([data, pd.DataFrame(columns=dynamicList)], sort=False) #Create dataframe to store file paths to dynamic CPGs



#Create dataframe to store all needed parameter values
paramValues = pd.concat([data, pd.DataFrame(columns=static),  pd.DataFrame(columns=SNODAS_SWEmmList), pd.DataFrame(columns=gridMET_minTempKList)], sort=False)



#Get static CPG values
points = data.USGS_Albers #Get list of data points

for param in static:

    paramCPG = os.path.join(CPGdir, "{0}_HUC{1}_CPG.tif".format(param, HUC)) #Build path to CPG file
    print(paramCPG)
    with rs.open(paramCPG) as ds:
        CPGvalues = ds.sample(points) #Read the parameter CPG at all data points

        #Add CPG values to dataframe
        for index, row in paramValues.iterrows():
            paramValues.at[index, param]= next(CPGvalues)[0]
            


opencount = 0

#Get dynamic CPG values

monthList = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

dynamicParams = [("SNODAS_SWEmm", SNODAS_SWEmm_fcn), ("gridMET_minTempK", gridMET_minTempK_fcn)]
#dynamicParams = [("gridMET_minTempK", gridMET_minTempK_fcn) ]

for index, row in paramValues.iterrows():

    obsYear = row['Year']
    obsMonth = row['Month']

    
    for paramName,paramF in dynamicParams:

        print(paramName)
        CPGdict = paramF(HUC, obsYear, obsMonth)
        
        for key, value in CPGdict.items():
            
            dynamicPaths.at[index, "{0}_{1}".format(paramName, key)]= value #Add the file path to the data frame

            #print("{0}_{1}".format(paramName, key))

            paramCPG = value
            coords = row['USGS_Albers']

            if os.path.isfile(paramCPG):
                with rs.open(paramCPG) as ds:

                    CPGvalues = ds.sample([coords],1)
                    opencount = opencount + 1 
                    try:
                        CPGval = next(CPGvalues)
                        paramValues.at[index, "{0}_{1}".format(paramName, key)]= CPGval[0]
                    except:
                        print("Error getting CPG value")
            else:
                print("Error file not found: {0}".format(paramCPG))



#Need code to loop over list of dynamic CPGs, get a list of coordinates asssociate with that CPG, pull the CPG values, then write to values to the output dataframe
newcount = 0
#Loop over each columns of dynamic parameters
for col in dynamicList:

    pathList = dynamicPaths[col].unique() #Get list of unique CPG paths in the column

    for path in pathList:
        rows = dynamicPaths.loc[dynamicPaths[col] == path] #Select rows with the current path
        points = rows['USGS_Albers'] #Get list of data points associated with the current path

        if os.path.isfile(path):
            with rs.open(path) as ds:
                CPGvalues = ds.sample(points) #Read the parameter CPG at all data points
                newcount = newcount + 1 
                #Add CPG values to dataframe
                for index, row in rows.iterrows():
                    dynamicPaths.at[index, param]= next(CPGvalues)[0]

        else:
                print("Error file not found: {0}".format(path))






paramValues.to_csv("../work/1002/obsTestParams.csv")
dynamicPaths.to_csv("../work/1002/obsTestParams_new.csv")

#print(dynamicPaths)
print(static)
print(dynamic)
print("{0} files opened".format(opencount))
print("{0} files opened".format(newcount))
