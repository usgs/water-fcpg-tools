import dbf
import os

paramtables = ["../data/cov/static/Soils/DrainageClass.dbf"]

#Convert dbfs to csvs
for paramtable in paramtables:

    db = dbf.Table(paramtable)
    dbf.export(db)