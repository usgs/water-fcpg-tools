import dbf
import os
import pandas as pandas
import numpy as np

paramtables = ["../data/cov/static/Soils/DrainageClass.dbf"]

outDir = "../data/cov/static/Soils/work"

#Convert dbfs to csvs
for paramtable in paramtables:


    paramName = os.path.splitext(os.path.basename(paramtable))[0]
    

    csvName = os.path.join(outDir, paramName + ".csv") #Create csv file
    print(csvName)

    db = dbf.Table(paramtable)
    db.open()

    dbf.export(db, csvName, header = True)

    df = pd.read_csv(csvName)

    print(df)

    

