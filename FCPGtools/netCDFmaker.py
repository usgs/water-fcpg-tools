# Based on code from Rich Signell
# Convert a group of GDAL readable grids to a NetCDF Time Series.
#
# metaDict = {
# 	'title':'',
# 	'institution':'',
# 	'source':'',
# 	'id':'',
# 	'naming_authority':'',
# 	'references':'',
# 	'comment':'',
# 	'history':'',
# 	'license':'', 
# 	'acknowledgement':'', # 
# 	'metadata_link':'', 
# 	'date_creates':'',
# 	'creator_type':'',
# 	'creator_email':'',
# 	'creator_name':'',
# 	'creator_url':'',
# 	'creator_institution':'',
# 	'publisher_type':'',
# 	'publisher_name':'',
# 	'publisher_email':'',
# 	'publisher_url':'',
# 	'publisher_institution':'', 
# 	'var_name':'Tmin',
# 	'units':'K',
# 	'add_offset':0.0,
# 	'standard_name':'min_temperature',
# 	'long_name':'minimum monthly temperature',
# 	'grid_mapping':'crs',
# 	'scale_factor':1.0,
# 	'coverage_content_type':''
# 	}

import numpy as np
import datetime as dt
import rasterio as rs
import os
import netCDF4
import sys
import glob
import time

def buildNC(inDir, outFile, metaDict, cl=9, profile = None):
	'''Build netCDF file from a stack of GeoTiffs.

	Parameters
	----------
	inDir : str
		Directory with geotiff files to be converted, specified as '/dir/here/\*.tif'
	outFile : str
		Output filename with '.nc' included.
	metaDict : dict
		Metadata dictionary used to populate fields in the netCDF. See Notes below for a description of fields to include.
	cl : int
		Compression level, 1-9. A higher value will result in a smaller output file, but will take longer.
	profile : dict (optional)
		Projection parameters to make the NetCDF file CF compliant. Defaults to USGS Albers Equal Area if nothing is supplied.

	Returns
	-------
	NetCDF : file
		A NetCDF file at *outFile*.

	Notes
	-----
	*Metadata Dictionary*
	
	The metadata dictionary is expecting a particular set of keys to specify the metadata fields within the netCDF file being generated. These fields were chosen to make the resulting netCDF file compliant with the Climate and Forecast and the Data Discovery metadata conventions. Fields are described below, many descriptions are the same as http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#description-of-file-contents or http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery_1-3. 

	title
		A succinct description of what is in the dataset.
	institution
		Specifies where the original data was produced.
	source
		The method of production of the original data. If it was model-generated, source should name the model and its version, as specifically as could be useful. If it is observational, source should characterize it (e.g., "surface observation" or "radiosonde").
	id 
		An identifier for the data set, provided by and unique within its naming authority. The combination of the "naming authority" and the "id" should be globally unique, but the id can be globally unique by itself also. IDs can be URLs, URNs, DOIs, meaningful text strings, a local key, or any other unique string of characters. The id should not include white space characters.
	naming_authority
		The organization that provides the initial id (see above) for the dataset. The naming authority should be uniquely specified by this attribute. We recommend using reverse-DNS naming for the naming authority; URIs are also acceptable. Example: 'edu.ucar.unidata'.
	references
		Published or web-based references that describe the data or methods used to produce it.
	comment
		Miscellaneous information about the data or methods used to produce it.
	history
		Provides an audit trail for modifications to the original data. Well-behaved generic netCDF filters will automatically append their name and the parameters with which they were invoked to the global history attribute of an input netCDF file. We recommend that each line begin with a timestamp indicating the date and time of day that the program was executed.
	license
		Provide the URL to a standard or specific license, enter "Freely Distributed" or "None", or describe any restrictions to data access and distribution in free text.
	acknowledgement
		A place to acknowledge various types of support for the project that produced this data.
	metadata_link
		A URL that gives the location of more complete metadata. A persistent URL is recommended for this attribute.
	date_created
		The date on which this version of the data was created. (Modification of values implies a new version, hence this would be assigned the date of the most recent values modification.) Metadata changes are not considered when assigning the date_created. The ISO 8601:2004 extended date format is recommended, as described in the Attribute Content Guidance section.
	creator_type
		Specifies type of creator with one of the following: 'person', 'group', 'institution', or 'position'. If this attribute is not specified, the creator is assumed to be a person.
	creator_email
		The email address of the person (or other creator type specified by the creator_type attribute) principally responsible for creating this data.
	creator_name
		The name of the person (or other creator type specified by the creator_type attribute) principally responsible for creating this data.
	creator_url
		The URL of the person (or other creator type specified by the creator_type attribute) principally responsible for creating this data.
	creator_institution
		The institution of the creator; should uniquely identify the creator's institution. This attribute's value should be specified even if it matches the value of publisher_institution, or if creator_type is institution.
	publisher_type
		Specifies type of publisher with one of the following: 'person', 'group', 'institution', or 'position'. If this attribute is not specified, the publisher is assumed to be a person.
	publisher_name
		The name of the person (or other entity specified by the publisher_type attribute) responsible for publishing the data file or product to users, with its current metadata and format.
	publisher_email
		The email address of the person (or other entity specified by the publisher_type attribute) responsible for publishing the data file or product to users, with its current metadata and format.
	publisher_url
		The URL of the person (or other entity specified by the publisher_type attribute) responsible for publishing the data file or product to users, with its current metadata and format.
	publisher_institution
		The institution that presented the data file or equivalent product to users; should uniquely identify the institution. If publisher_type is institution, this should have the same value as publisher_name.
	var_name
		Variable name given to the dataset. For example minimum temperature would be Tmin.
	units
		Unit value associated with quantity described by the dataset.
	add_offset
		Offset value use with the data, usually 0.0 if no offset is used with the data.
	standard_name
		Short name associated with the dataset.
	long_name
		More descriptive name associated with the dataset.
	grid_mapping
		The way data values are mapped to a grid, usually 'crs'.
	scale_factor
		Numeric value the data are scaled by to save space, usually 1.0 if data are not scaled.
	coverage_content_type
		An ISO 19115-1 code to indicate the source of the data (image, thematicClassification, physicalMeasurement, auxiliaryInformation, qualityInformation, referenceInformation, modelResult, or coordinate).

	*Profile*
	
	The projection parameters needed and values for USGS Albers Equal Area (AEA) are supplied below.

	grid_mapping_name ('albers_conical_equal_area')
		The name of the projection to use as a string.
	standard_parallel ([45.5, 29.5])
		Parallels for the projection as a list of floats. May differ for non-AEA projections; however, this work should be done with equal-area projections.
	latitude_of_projection_origin (23.0)
		Origin latitude as a float.
	longitude_of_central_meridian (-96.0)
		Central Meridian as a float.
	false_easting (0)
		Flase easting parameter as a float.
	false_northing (0)
		False northing parameter as a float.
	semi_major_axis (6378137.0)
		Ellipse parameter as a float.
	inverse_flattening (298.257222101)
		Ellipse parameter as a float.
	unit ('m')
		Map units to use for the projection as a string.
	wkt
		Well known text (WKT) representation of the above projection parameters, e.g. 'PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\", GEOGCS[\"GCS_North_American_1983\", DATUM[\"D_North_American_1983\", SPHEROID[\"GRS_1980\",6378137.0,298.257222101]], PRIMEM[\"Greenwich\",0.0], UNIT[\"Degree\",0.0174532925199433]], PROJECTION[\"Albers\"], PARAMETER[\"False_Easting\",0.0], PARAMETER[\"False_Northing\",0.0], PARAMETER[\"Central_Meridian\",-96.0], PARAMETER[\"Standard_Parallel_1\",29.5], PARAMETER[\"Standard_Parallel_2\",45.5], PARAMETER[\"Latitude_Of_Origin\",23.0], UNIT[\"Meter\",1]]'
	'''
	strt = dt.datetime.now() # start timing

	#inDir = sys.argv[1]
	#netCDFparam = sys.argv[2]
	#outFile = sys.argv[3]


	#outFile = 'data/gridMET_minTempK_HUC1003_CPG.nc'
	#netCDFparam = 'gridMET_minTempK'
	#inDir = "data/cpgs_to_netCDF/*.tif"
	#cl = 9

	if profile is None: # set the profile to USGS AEA if nothing is supplied.
		profile = {
			'grid_mapping_name' : 'albers_conical_equal_area',
			'standard_parallel' : [45.5, 29.5],
			'latitude_of_projection_origin' : 23.0,
			'longitude_of_central_meridian' : -96.0,
			'false_easting' : 0,
			'false_northing' : 0,
			'semi_major_axis' : 6378137.0,
			'inverse_flattening' : 298.257222101,
			'unit' : 'm',
			'wkt' : 'PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",GEOGCS[\"GCS_North_American_1983\",DATUM[\"D_North_American_1983\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-96.0],PARAMETER[\"Standard_Parallel_1\",29.5],PARAMETER[\"Standard_Parallel_2\",45.5], PARAMETER[\"Latitude_Of_Origin\",23.0], UNIT[\"Meter\",1]]'
				}


	# refer to http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery_1-3 and http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#description-of-file-contents for metadata entry descriptions.

	# enforce some defaults if they are not present
	if 'Conventions' not in metaDict.keys():
		metaDict['Conventions'] = 'CF-1.7\nDD-1.3' # conventions this was written around

	if 'grid_mapping' not in metaDict.keys():
		metaDict['grid_mapping'] = 'crs' # mapped to projected grid

	if 'scale_factor' not in metaDict.keys():
		metaDict['scale_factor'] = 1.0 # set scale at 1.

	if 'add_offset' not in metaDict.keys():
		metaDict['add_offset'] = 0.0 # no offset

	if 'history' not in metaDict.keys():
		metaDict['history'] = '' # start with blank history

	files = glob.glob(inDir) # there probably should be some more work here to parse time and order the files by time so that the loop works properly at the end.

	assert len(files) > 0 # check that there are files to process
	templateFile = files [0] # use first file as the template

	np.set_printoptions(threshold=sys.maxsize)

	with rs.open(templateFile) as ds:
		NoData = ds.nodata
		dataType = ds.dtypes[0] #Get datatype of first band
		xsize, ysize = ds.res #Get  cell size
	
		#Get bounding coordinates of the raster
		Xmin = ds.transform[2]
		Ymax = ds.transform[5]
		Xmax = Xmin + xsize*ds.width
		Ymin = Ymax - ysize*ds.height
	
		a = ds.transform
		nrow,ncol = ds.shape

	# make arrays of rows and columns
	nx = np.arange(ncol)
	ny = np.arange(nrow)
	print("Grid Shape:")
	print("\tncol:",ncol)
	print("\tnrow:",nrow)

	# translate the rows and columns to x,y
	x,tmp = rs.transform.xy(rows = np.repeat(0,len(nx)),cols = nx, transform=a)
	tmp,y = rs.transform.xy(rows = ny, cols = np.repeat(0,len(ny)), transform=a)
	del tmp

	print("\tx:",len(x))
	print("\ty:",len(y))

	print(dataType)
	if dataType == 'float32':
		ncDataType = 'f4'
	elif dataType == 'int32':
		ncDataType = 'i4'
	else:
		print("Error: unsupported data type")
		sys.exit(0)

	basedate = dt.datetime(1900,1,1,0,0,0) #Set basedate to January 1, 1900

	# create NetCDF file
	nco = netCDF4.Dataset(outFile,'w',clobber=True, format = 'NETCDF4_CLASSIC')
	# try to populate the metadata
	try:
		nco.title = metaDict['title']
		nco.institution = metaDict['institution']
		nco.source = metaDict['source']
		nco.id = metaDict['id']
		nco.naming_authority = metaDict['naming_authority']
		nco.references = metaDict['references']
		nco.comment = metaDict['comment']
		nco.history = metaDict['history']
		nco.license = metaDict['license']
		nco.acknowledgement = metaDict['acknowledgement']
		nco.metadata_link = metaDict['metadata_link']
		
		nco.date_created = metaDict['date_created']
		nco.creator_type = metaDict['creator_type']
		nco.creator_name = metaDict['creator_name']
		nco.creator_email = metaDict['creator_email']
		nco.creator_url = metaDict['creator_url']
		nco.creator_institution = metaDict['creator_institution']

		nco.publisher_type = metaDict['publisher_type']
		nco.publisher_name = metaDict['publisher_name']
		nco.publisher_email = metaDict['publisher_email']
		nco.publisher_url = metaDict['publisher_url']
		nco.publisher_institution = metaDict['publisher_institution']
	
	except:
		print('Metadata incomplete.')

	nco.Conventions=metaDict['Conventions']

	# chunking is optional, but can improve access: 
	# (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
	#chunk_lon=16
	#chunk_lat=16
	#chunk_time=12

	# create dimensions, variables and attributes:
	nco.createDimension('y',nrow)
	nco.createDimension('x',ncol)
	nco.createDimension('time', None)

	# time axis
	timeo = nco.createVariable('time','f4',('time'))
	timeo.units = 'days since 1900-01-01 00:00:00'
	timeo.standard_name = 'time'

	# projected vertical coordinates (latitude)
	yo = nco.createVariable('y','f4',('y'),zlib=True, complevel=cl, shuffle = True)
	yo.units = 'm'
	yo.standard_name = 'projection_y_coordinate'

	# projected horizontal coordinates (longitude)
	xo = nco.createVariable('x','f4',('x'),zlib=True, complevel=cl, shuffle = True)
	xo.units = 'm'
	xo.standard_name = 'projection_x_coordinate'

	#write lon,lat
	xo[:]=x
	yo[:]=y

	#Define coordinate system
	crso = nco.createVariable('crs','i4') #i4 = 32 bit signed int
	crso.grid_mapping_name= profile['grid_mapping_name']
	#crso.standard_parallel_1 = 29.5
	#crso.standard_parallel_2 = 45.5
	crso.standard_parallel = profile['standard_parallel'] 
	crso.latitude_of_projection_origin = profile['latitude_of_projection_origin']
	crso.longitude_of_central_meridian = profile['longitude_of_central_meridian']
	crso.false_easting = profile['false_easting']
	crso.false_northing = profile['false_northing']
	crso.semi_major_axis = profile['semi_major_axis']
	crso.inverse_flattening = profile['inverse_flattening']
	crso.unit = profile['unit']
	crso.crs_wkt = profile['wkt']
	crso.spatial_ref = profile['wkt']

	# create short integer variable for temperature data, with chunking
	tmno = nco.createVariable(metaDict['var_name'], ncDataType,  ('time', 'y', 'x'), zlib=True, fill_value=NoData, complevel=cl, shuffle = True) #Create variable, compress with gzip (zlib=True)
	tmno.units = metaDict['units']
	tmno.scale_factor = metaDict['scale_factor']
	tmno.add_offset = metaDict['add_offset']
	tmno.long_name = metaDict['long_name']
	tmno.standard_name = metaDict['standard_name']
	tmno.grid_mapping = metaDict['grid_mapping']
	coverage_content_type = metaDict['coverage_content_type']
	tmno.set_auto_maskandscale(False)

	itime=0
	for name in sorted(files):
		#Check if file has correct parameter name
		baseName = name.split('/')[-1]
		source = baseName.split("_")[0]
		param = baseName.split("_")[1]


		year = int(name.split('/')[-1].split('_')[-5])
		month = int(name.split('/')[-1].split('_')[-4])
		day = int(name.split('/')[-1].split('_')[-3])
		#print(year,month,day)
		date = dt.datetime(year, month, day, 0, 0, 0) # set base date
		dtime=(date-basedate).total_seconds()/86400.
		timeo[itime]=dtime

		#Try reading with rasterio
		with rs.open(name) as ds: # load accumulated data and no data rasters
			tmno[itime,:,:] = ds.read(1)

		itime=itime+1

	nco.close()

	print((dt.datetime.now()-strt))
	return None
