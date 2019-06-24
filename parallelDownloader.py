def downloadNHDPlusRaster(HUC4, fileDir):
    '''
    Inputs:
        
        HUC4 - 4 digit HUC to download NHDPlus raster data for
        fileDir - Directory in which to save NHDPlus data

    Outputs:
        NHDPlus raster files saved to directory

    '''
    compressedFile = os.path.join(fileDir, str(HUC4) + "_RASTER.7z")
    print("Downloading File: " + compressedFile)
    urllib.request.urlretrieve("https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHDPlus/HU4/HighResolution/GDB/NHDPLUS_H_%s_HU4_RASTER.7z"%str(HUC4), compressedFile)

    print("Extracting File...")
    os.system("7za x {0} -o{1}".format(compressedFile,fileDir))

    
