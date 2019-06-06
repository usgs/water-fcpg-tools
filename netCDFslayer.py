# Script to destroy the netCDF file Roy got from gridMET

with rs.open(paramRast) as ds: # load parameter raster
        data = ds.read(1)
        profile = ds.profile
        paramNoData = ds.nodata