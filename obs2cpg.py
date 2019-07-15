import pandas as pd

obsFile = "../data/observations/flowPerm_07152019.txt"

CPGdir = "../CPGs/1002"

data = pd.read_csv(obsFile)

data.Date =  pd.to_datetime(data.Date, format='%m/%d%/Y %H:%M:%S.%f')


print(data.Date)