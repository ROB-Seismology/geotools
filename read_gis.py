"""
Read GIS files in various formats
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import dict

try:
	## Python 2
	basestring
except:
	## Python 3
	basestring = str


import os
from collections import OrderedDict
import ogr, osr

from .coordtrans import WGS84, LAMBERT1972



def get_available_formats():
	"""
	Return list of available vector GIS formats
	"""
	gis_formats = []

	for i in range(ogr.GetDriverCount()):
		driver = ogr.GetDriver(i)
		driverName = driver.GetName()
		if not driverName in gis_formats:
			gis_formats.append(driverName)

	return sorted(gis_formats)


def read_gis_file(GIS_filespec, layer_num=0, out_srs=WGS84, encoding="guess",
				attribute_filter="", fix_mi_lambert=True, verbose=True):
	"""
	Read GIS file.

	:param GIS_filespec:
		str, full path to GIS file to read
	:param layer_num:
		int, index of layer to read (default: 0)
	:param out_srs:
		instance of :class:`ogr.SpatialReference`
		spatial reference system into which coordinates will be transformed
		If None, native spatial reference system will be used
		(default: WGS84)
	:param encoding:
		str, unicode encoding
		(default: "guess", will try to guess, but this may fail)
	:param attribute_filter:
		str, attribute query string to be used when fetching features.
		Only features for which the query evaluates as true will be returned.
		The query string should be in the format of an SQL WHERE clause.
		Note that string values in the query must be single-quoted!

		Alternatively, attribute filter may be a dict, mapping field
		names to lists of values.
		Note: multiple values mapped to a column name will act as logical
		OR, multiple keys will act as logical AND operator.
		(default: "")
	:param fix_mi_lambert:
		bool, whether or not to apply spatial reference system fix for
		old MapInfo files in Lambert 1972 system
		(default: True)
	:param verbose:
		bool, whether or not to print information while reading
		GIS table (default: True)

	:return:
		list of dictionaries corresponding to GIS records.
		Each record contains the following keys:
		- 'obj': corresponding value is instance of :class:`osgeo.ogr.Geometry`
			with all coordinates in spatial reference system in :param:`out_srs`
		- '#': sequence number
		- keys corresponding to data attribute names
		Note that keys and string values are decoded into unicode
		if :param:`encoding' is not set
	"""
	ds = ogr.Open(GIS_filespec, 0)
	if ds is None:
		raise Exception("OGR failed to open %s" % GIS_filespec)
	num_layers = ds.GetLayerCount()
	if verbose:
		print("Number of layers: %d" % num_layers)

	if isinstance(layer_num, int):
		layer_nums = [layer_num]
	elif layer_num is None:
		layer_nums = range(num_layers)

	records = []
	for layer_num in layer_nums:
		if layer_num < num_layers:
			layer = ds.GetLayer(layer_num)
		else:
			raise Exception("File contains less than %d layers!" % layer_num)

		## Try to guess encoding
		## See: https://nelsonslog.wordpress.com/2015/01/15/ogrpython-vs-unicode/
		## and https://github.com/openaddresses/machine/blob/e5099e5a23b8ab6571227c5f8487034c8a8b7cc2/openaddr/conform.py#L213
		# TODO: isn't there a more robust way?
		# See http://gis.stackexchange.com/questions/7608/shapefile-prj-to-postgis-srid-lookup-table
		# for shapefiles
		if encoding == "guess":
			from locale import getpreferredencoding
			ogr_recoding = layer.TestCapability(ogr.OLCStringsAsUTF8)
			is_shapefile = ds.GetDriver().GetName() == 'ESRI Shapefile'

			encoding = ((ogr_recoding and 'UTF-8')
				or (is_shapefile and 'ISO-8859-1')
				or getpreferredencoding())

		## Get all field names
		field_names = []
		ld = layer.GetLayerDefn()
		for field_index in range(ld.GetFieldCount()):
			fd = ld.GetFieldDefn(field_index)
			field_names.append(fd.GetName())

		## Set up transformation between table coordsys and wgs84
		tab_srs = layer.GetSpatialRef()

		## Hack to fix earlier MapInfo implementation of Lambert1972
		if fix_mi_lambert:
			wkt = tab_srs.ExportToWkt()
			if (os.path.splitext(GIS_filespec)[-1].upper() == ".TAB" and
				('DATUM["Belgium_Hayford' in wkt or 'DATUM["MIF 999' in wkt
				or 'TOWGS84[0,0,0,0,0,0,0]' in wkt)):
				if tab_srs.IsProjected():
					print("Fixing older MapInfo implementation of Lambert1972...")
					tab_srs = LAMBERT1972
				else:
					# TODO
					print("Warning: older MapInfo implementation of Lambert1972, "
							"coordinates may be shifted!")
				#tab_srs.CopyGeogCSFrom(LAMBERT1972)

		if out_srs and not tab_srs.IsSame(out_srs):
			coordTrans = osr.CoordinateTransformation(tab_srs, out_srs)
		else:
			coordTrans = None

		## Apply attribute filter
		if attribute_filter:
			if isinstance(attribute_filter, dict):
				subqueries = []
				for key, values in attribute_filter.items():
					field_index = field_names.index(key)
					fd = ld.GetFieldDefn(field_index)
					if fd.GetType() == ogr.OFTString:
						values = ["'%s'" % val for val in values]
					q = "%s in (%s)" % (key, ','.join(values))
					subqueries.append(q)
				attribute_filter = ' AND '.join(subqueries)
				## Note: str for PY2/3 compatibility
				attribute_filter = str(attribute_filter)
			retval = layer.SetAttributeFilter(attribute_filter)
			if retval != 0:
				print("Warning: attribute filter failed, check your syntax!")

		## Loop over features in layer
		num_features = layer.GetFeatureCount()
		if verbose:
			print("Number of features in layer %d: %d" % (layer_num, num_features))

		## Note: because of attribute filter, only use GetNextFeature method
		## or iterate over layer
		for i, feature in enumerate(layer):
		#for i in range(num_features):
			feature_data = OrderedDict()
			#feature = layer.GetNextFeature()

			## Silently ignore empty rows
			if feature:
				feature_data['#'] = i
				## Get geometry
				## Note: we need to clone the geometry returned by GetGeometryRef(),
				## otherwise python will crash
				## See http://trac.osgeo.org/gdal/wiki/PythonGotchas
				try:
					geom = feature.GetGeometryRef().Clone()
				except:
					## Silently ignore
					pass
				else:
					geom.AssignSpatialReference(tab_srs)
					if coordTrans:
						geom.Transform(coordTrans)
					#geom.CloseRings()
					feature_data['obj'] = geom

					## Get feature attributes
					for i, field_name in enumerate(field_names):
						value = feature.GetField(i)
						## Convert field names and string values to unicode
						if encoding:
							if isinstance(field_name, bytes):
								field_name = field_name.decode(encoding)
							if isinstance(value, bytes):
								value = value.decode(encoding)
						feature_data[field_name] = value
					records.append(feature_data)
	return records


def read_gis_file_attributes(GIS_filespec, layer_num=0):
	"""
	Read GIS data attributes.

	:param GIS_filespec:
		str, full path to GIS file to read
	:param layer_num:
		int, index of layer to read (default: 0)

	:return:
		list of strings, attribute names.
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


def read_gis_file_shapes(GIS_filespec, layer_num=0):
	"""
	Read GIS shapes.

	:param GIS_filespec:
		str, full path to GIS file to read
	:param layer_num:
		int, index of layer to read (default: 0)

	:return:
		list of strings, GIS shapes.
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


def read_gis_file_srs(GIS_filespec, layer_num=0):
	"""
	Read GIS SRS.

	:param GIS_filespec:
		str, full path to GIS file to read
	:param layer_num:
		int, index of layer to read (default: 0)

	:return:
		instance of :class:`ogr.SpatialReference`
	"""
	ds = ogr.Open(GIS_filespec, 0)
	if ds is None:
		raise Exception("OGR failed to open %s" % GIS_filespec)
	num_layers = ds.GetLayerCount()

	if layer_num < num_layers:
		layer = ds.GetLayer(layer_num)
	else:
		raise Exception("File contains less than %d layers!" % layer_num)

	return layer.GetSpatialRef()
