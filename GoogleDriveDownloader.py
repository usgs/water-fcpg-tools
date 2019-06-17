import gdown
import os

urls = {1985:"https://drive.google.com/open?id=1bIwlx3ufdjWdSNIP7Aqsh7WXoKLBcqBw", 
1986:"https://drive.google.com/open?id=102zi-1it1yhMPUBmdzpjhlElV8mA4NLZ",
1987:"https://drive.google.com/open?id=1QMq1K6XUXKWIiNC74xjtsSt4ktX2iVWi",
1988:"https://drive.google.com/open?id=1M3D4a5eFo66yFHuR7_mDtuC5RJAiCGm7",
1989:"https://drive.google.com/open?id=1tuZTQY10wK1gtnhaCZqJQT_WXatHa8jv",
1990:"https://drive.google.com/open?id=15OGrPZyxckAwFY-j1R40smJvzRMk4de_",
1991:"https://drive.google.com/open?id=1vp1r96oNnmSDFFzBXJAKLe9shK8DsMHI",
1992:"https://drive.google.com/open?id=1wC_lmL7inhgWzcr7iLMJV9ui_PW0x_XC",
1993:"https://drive.google.com/open?id=1fsD2z3SJYEFudpjRU59KomKLz3AQSkDv",
1994:"https://drive.google.com/open?id=1JJ9PjOo7AUwotLOQ_H4-5wmEN2fb0A-r",
1995:"https://drive.google.com/open?id=1qI5ilF4VfOY70dmdoGOG3kMtLfYdXefm",
1996:"https://drive.google.com/open?id=1X9ZmI3F70tU94aJkEzZ3G4lAAowBRFlq",
1997:"https://drive.google.com/open?id=1YqmHQjbovpoaa-CzwZeybDGjG4Xp9ZI9",
1998:"https://drive.google.com/open?id=1jQuXHsY8b7cG9VlhUbOmKHKfImNd2TIu",
1999:"https://drive.google.com/open?id=1CGPJUvHTcm8Z3x_nvsOrLsHfrOvt-DpP",
2000:"https://drive.google.com/open?id=1JlwW5TGG38bnxDWiVP3TW8q25PVA8K1M",
2001:"https://drive.google.com/open?id=125BRk867eVg7eLcGHJV6Nx9rjrgMhwEF",
2002:"https://drive.google.com/open?id=1MXWlizOCuDOl5FDkbaN1fMky2yHBuYzv",
2003:"https://drive.google.com/open?id=1M97yPaiUb7-EtEz9dUSGfOZVOGnj_ui7",
2004:"https://drive.google.com/open?id=16LJXSVn-4CRO4b8bmlb8eQ7VM-7L6Ir8",
2005:"https://drive.google.com/open?id=1TEBBHg5epEhu0JGTwOk-DKlz4DJkSjk5",
2006:"https://drive.google.com/open?id=1UxiORTXeLn3MoNcZ3gG_MyXhnDUfujaN",
2007:"https://drive.google.com/open?id=1IgDqimQuyRO_b9IQmf3l1v6e-BvMfL--",
2008:"https://drive.google.com/open?id=1_S7wbSb-dbwal-Rw3pOkBhaq9YsTSaeM",
2009:"https://drive.google.com/open?id=1ODR6GjZapGqyuMZR6IOA9a_vWLvmYL8c",
2010:"https://drive.google.com/open?id=18Aa0A0WopQDBQkQfDERqfPXVxXjx7AIl",
2011:"https://drive.google.com/open?id=1a4LmA1OBCJudaRuJ_TqyKP3mTlqiqBHH",
2012:"https://drive.google.com/open?id=1t6Om3X7EiH9wp2GtZWPz4OQJpNhh57iA",
2013:"https://drive.google.com/open?id=1EFR2QZRMLkho1ggYaHqmE71LWEDEq9aT",
2014:"https://drive.google.com/open?id=1F49cNww-e8BIoirgvWcfZg8i9s1rvE4I",
2015:"https://drive.google.com/open?id=1WS5zUnm1mI8eUBsa0vpNzQ2eUvl5258n",
2016:"https://drive.google.com/open?id=14u29ALnWg1qZW86_S6IAMrsx4vag3yTj",
2017:"https://drive.google.com/open?id=1yFI_NAPHaPdAQgLsl-pHHeJZWZCcRCVd",
2018:"https://drive.google.com/open?id=1_HuvkKBAlEpMZsl2EVVtGL1oQrLkCfrZ"}

outDir = "../data/cov/NDVI"

HUC = 1002


for year, url in urls.iteritems():
    outName = "LANSAT_NVDI_{0}_00_00_HUC{1}.tif".format(year, HUC)

    outpath = os.path.join(outDir, outName)
    
    gdown.download(url, outpath, quiet=False)
