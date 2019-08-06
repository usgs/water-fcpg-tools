



def nan2nodata(inRast, outRast):
    """
    Inputs:
        inRast - Input raster file path

    Outputs:
        outRast - Output raster file path
    """

    print('Opening raster...')

    # load input data
    with rs.open(inRast) as ds:
        dat = ds.read(1)
        inNoData = ds.nodata
        profile = ds.profile.copy() # save the metadata for output later



    fix = np.nan_to_num(dat, nan=-9999)
    
    fix = fix.astype('float32')

    # edit the metadata
    profile.update({
                'dtype':'float32',
                'compress':'LZW',
                'profile':'GeoTIFF',
                'tiled':True,
                'sparse_ok':True,
                'num_threads':'ALL_CPUS',
                'nodata':-9999,
                'bigtiff':'IF_SAFER'})

    with rs.open(outRast,'w',**profile) as dst:
        dst.write(fix,1)
        print("Raster written to: {0}".format(outRast))
