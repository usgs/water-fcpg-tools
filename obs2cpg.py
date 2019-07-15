import pandas as pd

obsFile = "../data/observations/flowPerm_07152019.txt"

CPGdir = "../CPGs/1002"

data = pd.read_csv(obsFile)

print(data.Date.month)