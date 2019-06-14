import dbf
import os
import pandas as pandas
import numpy as np

paramtables = ["../data/cov/static/Soils/DrainageClass.dbf"]

#Convert dbfs to csvs
for paramtable in paramtables:

    db = dbf.Table(paramtable)
    dbf.export(db)

    #df = pd.read_csv()


