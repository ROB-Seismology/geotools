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

	ds = ogr.Open(GIS_filespec, 0)
	if ds is None:
		raise Exception("OGR failed to open %s" % GIS_filespec)
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

		## Silently ignore empty rows
		if feature:
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
				# TODO: convert strings to unicode based on charset in TAB definition
			records.append(feature_data)
	return records


def read_GIS_file_attributes(GIS_filespec, layer_num=0):
	"""
	Read GIS data attributes.

	:param GIS_filespec:
		String, full path to GIS file to read
	:param layer_num:
		Integer, index of layer to read (default: 0)

	:return:
		list of attribute names.
	"""
	ds = ogr.Open(GIS_filespec, 0)
	if ds is None:
		raise Exception("OGR failed to open %s" % GIS_filespec)
	num_layers = ds.GetLayerCount()

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

	return field_names


def read_GIS_file_shapes(GIS_filespec, layer_num=0):
	"""
	Read GIS shapes.

	:param GIS_filespec:
		String, full path to GIS file to read
	:param layer_num:
		Integer, index of layer to read (default: 0)

	:return:
		list of GIS shapes.
	"""
	ds = ogr.Open(GIS_filespec, 0)
	if ds is None:
		raise Exception("OGR failed to open %s" % GIS_filespec)
	num_layers = ds.GetLayerCount()

	if layer_num < num_layers:
		layer = ds.GetLayer(layer_num)
	else:
		raise Exception("File contains less than %d layers!" % layer_num)

	num_features = layer.GetFeatureCount()
	shapes = set()
	for i in range(num_features):
		feature = layer.GetNextFeature()

		## Silently ignore empty rows
		if feature:
			## Get geometry
			geom = feature.GetGeometryRef().Clone()
			geom_type = geom.GetGeometryName()
			if geom_type in ("POINT", "MULTIPOINT"):
				shapes.add("points")
			elif geom_type in ("LINESTRING", "MULTILINESTRING"):
				shapes.add("polylines")
			elif geom_type in ("POLYGON", "MULTIPOLYGON"):
				shapes.add("polygons")

	return list(shapes)
