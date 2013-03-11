import os
import ogr, osr



def read_GIS_file(GIS_filespec, layer_num=0, verbose=True):
	"""
	Read GIS file.

	:param GIS_filespec:
		String, full path to GIS file to read
	:param layer_num:
		Integer, index of layer to read (default: 0)
	:param verbose:
		Boolean, whether or not to print information while reading
		GIS table (default: True)

	:return:
		list of dictionaries corresponding to GIS records.
		Each record contains the following keys:
		- 'obj': corresponding value is instance of :class:`osgeo.ogr.Geometry`
			with all coordinates in WGS84 reference system
		- keys corresponding to data attribute names
	"""
	## Construct WGS84 projection system
	wgs84 = osr.SpatialReference()
	wgs84.SetWellKnownGeogCS("WGS84")

	## Select driver based on file extension
	if os.path.splitext(GIS_filespec)[1].upper() == ".TAB":
		ogr_driver = ogr.GetDriverByName("MapInfo File")
	elif os.path.splitext(GIS_filespec)[1].upper() == ".SHP":
		ogr_driver = ogr.GetDriverByName("ESRI Shapefile")

	ds = ogr_driver.Open(GIS_filespec)
	num_layers = ds.GetLayerCount()
	if verbose:
		print("Number of layers: %d" % num_layers)
	if layer_num < num_layers:
		layer = ds.GetLayer(layer_num)
	else:
		raise Exception("File contains less than %d layers!" % layer_num)

	## Get all field names
	field_names = []
	ld = layer.GetLayerDefn()
	for field_index in range(ld.GetFieldCount()):
		fd = ld.GetFieldDefn(field_index)
		field_names.append(fd.GetName())

	## Set up transformation between table coordsys and wgs84
	tab_sr = layer.GetSpatialRef()
	coordTrans = osr.CoordinateTransformation(tab_sr, wgs84)

	## Loop over features in layer
	num_features = layer.GetFeatureCount()
	if verbose:
		print("Number of features in layer %d: %d" % (layer_num, num_features))
	records = []
	for i in range(num_features):
		feature_data = {}
		feature = layer.GetNextFeature()

		## Get geometry
		## Note: we need to clone the geometry returned by GetGeometryRef(),
		## otherwise python will crash
		## See http://trac.osgeo.org/gdal/wiki/PythonGotchas
		geom = feature.GetGeometryRef().Clone()
		geom.AssignSpatialReference(tab_sr)
		geom.Transform(coordTrans)
		#geom.CloseRings()
		feature_data['obj'] = geom

		## Get feature attributes
		for field_name in field_names:
			feature_data[field_name] = feature.GetField(field_name)
		records.append(feature_data)
	return records

