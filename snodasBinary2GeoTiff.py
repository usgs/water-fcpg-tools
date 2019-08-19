#Script for converting SNODAS binary files to geotiffs

import os
import subprocess

#inDir = "../../../../cxfs/projects/usgs/water/wymtwsc/georad/prosper/data/cov/snodas"
inDir = "../data/cov/snodas"
"""
filelist = [] # Initialize list

for path, subdirs, files in os.walk(inDir):
    for name in files:
        #Check if file is .tif, and if so add it to covariate list
        if os.path.splitext(name)[1] == ".dat":
                filelist.append(os.path.join(path, name))

"""
filelist = ["../data/cov/snodas/us_ssmv11034tS__T0001TTNATS2006030105HP001.dat", "../data/cov/snodas/us_ssmv11034tS__T0001TTNATS2006070105HP001.dat"] #Correct a couple files
                
for f in filelist:
    
    fname = os.path.splitext(os.path.basename(f))[0] #Get the name of the file
    fext = os.path.splitext(os.path.basename(f))[1] #Get the extension of the file
    
    paramCode = int(fname[8:12]) #Get the parameter code
    print(paramCode)
    
    if paramCode == 1034:
                
                #Get the other information I care about
                year = fname[27:31]
                month = fname[31:33]
                day = fname[33:35]
                
                #Create a new, sensible file name
                
                newName = "SNODAS_SWEmm_{0}_{1}_{2}.tif".format(year, month, day)
                
                headerFile = os.path.join(inDir, "{0}.hdr".format(fname)) # Create path to the new header file
                
                print(newName)
                print(headerFile)
                
                newFile = os.path.join(inDir, newName)
                
                
                with open(headerFile, 'w+') as h:
        
                    #Write header file
                    h.writelines("ENVI\n")
                    h.writelines("samples = 6935\n")
                    h.writelines("lines   = 3351\n")
                    h.writelines("bands   = 1\n")
                    h.writelines("header offset = 0\n")
                    h.writelines("file type = ENVI Standard\n")
                    h.writelines("data type = 2\n")
                    h.writelines("interleave = bsq\n")
                    h.writelines("byte order = 1\n")
                
                
                #Run some GDAL magic
                
                try:
                    

                    cmd = "gdal_translate -of GTiff -a_srs \"+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs\" -a_nodata -9999 -a_ullr  -124.73333333 52.87500000 -66.94166667 24.95000000 {0} {1}".format(f, newFile)
                    print(cmd)
                    result = subprocess.run(cmd, shell = True)
                    result.stdout

                    print('Parameter reprojected to: %s'%newName)
                except:
                    print('Error Converting File')
                    traceback.print_exc()
                
                