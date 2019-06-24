import os
import urllib.request

fileDir = "../data/cov/minTempNCDF"

for year in range(1979, 2018):

    dataFile = os.path.join(fileDir, "tmmn_{0}.nc".format(year))
    print("Downloading File: " + dataFile)
    urllib.request.urlretrieve("https://www.northwestknowledge.net/metdata/data/tmmn_{0}.nc".format(year), dataFile)


