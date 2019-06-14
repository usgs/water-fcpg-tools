import dbf
import os
import pandas as pandas
import numpy as np

paramtables = ["../data/cov/static/Soils/DrainageClass.dbf"]

outDir = "../data/cov/static/Soils/work"

#Convert dbfs to csvs
for paramtable in paramtables:

    db = dbf.Table(paramtable)
    dbf.export(db)

    paramName = os.path.splitext(os.path.basename(paramtable))[0]
    print(paramName)

    csvName = os.path.join(outDir, paramName + ".csv") #Create csv file

    db = dbf.Table('temptable.dbf')
    db.open()

    dbf.export(db, csvName, header = True)

    #df = pd.read_csv()


