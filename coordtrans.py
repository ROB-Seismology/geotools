import os
import numpy as np
import ogr
import osr


## Construct WGS84 projection system
wgs84 = osr.SpatialReference()
wgs84.SetWellKnownGeogCS("WGS84")

## Construct Lambert projection system
lambert_wkt = 'PROJCS["Belgian National System (7 parameters)",GEOGCS["unnamed",DATUM["Belgian 1972 7 Parameter",SPHEROID["International 1924",6378388,297],TOWGS84[-99.059,53.322,-112.486,0.419,-0.83,1.885,0.999999]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",49.8333339],PARAMETER["standard_parallel_2",51.1666672333],PARAMETER["latitude_of_origin",90],PARAMETER["central_meridian",4.3674866667],PARAMETER["false_easting",150000.013],PARAMETER["false_northing",5400088.438],UNIT["Meter",1.0]]'
#lambert_wkt = 'PROJCS["Belge 1972 / Belgian Lambert 72",GEOGCS["Belge 1972",DATUM["Reseau_National_Belge_1972",SPHEROID["International 1924",6378388,297,AUTHORITY["EPSG","7022"]],TOWGS84[106.869,-52.2978,103.724,-0.33657,0.456955,-1.84218,1],AUTHORITY["EPSG","6313"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4313"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",51.16666723333333],PARAMETER["standard_parallel_2",49.8333339],PARAMETER["latitude_of_origin",90],PARAMETER["central_meridian",4.367486666666666],PARAMETER["false_easting",150000.013],PARAMETER["false_northing",5400088.438],AUTHORITY["EPSG","31370"],AXIS["X",EAST],AXIS["Y",NORTH]]'
lambert1972 = osr.SpatialReference()
lambert1972.ImportFromWkt(lambert_wkt)


def get_epsg_srs(epsg_code):
	"""
	Get spatial reference from EPSG code

	:param epsg_code:
		str or int, EPSG code (e.g., "EPSG:3857", "3857" or 3857)

	:return:
		Instance of :class:`osr.SpatialReference`
	"""
	if isinstance(epsg_code, (str, unicode)):
		if epsg_code[:5] == "EPSG:":
			epsg_code = epsg_code.split(':')[1]
		epsg_code = int(epsg_code)
	srs = osr.SpatialReference()
	srs.ImportFromEPSG(epsg_code)
	return srs


def get_utm_spec(lon, lat):
	"""
	Determine UTM zone and hemisphere

	:param lon:
		Float, longitude
	:param lat:
		Float, latitude

	:return:
		(Int, Str) tuple: UTM zone, hemisphere
	"""
	## Constrain longitude between -180 and 180
	lon = (lon + 180) - int((lon + 180) / 360) *360 - 180
	utm_zone = int((lon + 180) / 6 ) + 1

	if lat < 0:
		utm_hemisphere = "S"
	else:
		utm_hemisphere = "N"

	return (utm_zone, utm_hemisphere)


def get_utm_srs(utm_spec="UTM31N"):
	"""
	:param utm_spec:
		String, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")
		or
		(Int, Str) tuple with UTM zone and hemisphere

	:return:
		Instance of :class:`osr.SpatialReference`
	"""
	if not isinstance(utm_spec, (str, unicode)):
		utm_zone, hemisphere = utm_spec[:2]
		utm_spec = "UTM%d%s" % (utm_zone, hemisphere)
	utm_hemisphere = utm_spec[-1]
	utm_zone = int(utm_spec[-3:-1])
	utm = osr.SpatialReference()
	utm.SetProjCS("UTM %d (WGS84) in northern hemisphere." % utm_zone)
	utm.SetWellKnownGeogCS("WGS84")
	utm.SetUTM(utm_zone, {"N": True, "S": False}[utm_hemisphere])
	return utm


def transform_point(source_srs, target_srs, x, y, z=None):
	"""
	Transform (reproject) a single point.

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param x:
		float, longitude or easting
	:param y:
		float, latitude or northing
	:param z:
		float, elevation in m (default: None):

	:return:
		(x, y, [z]) tuple of transformed coordinates
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

	if z is None:
		return ct.TransformPoint(x, y)[:2]
	else:
		return ct.TransformPoint(x, y, z)


def transform_coordinates(source_srs, target_srs, coord_list):
	"""
	Transform (reproject) a list of coordinates.

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param coord_list:
		List of (lon, lat, [z]) or (easting, northing, [z]) tuples

	:return:
		List of transformed coordinates (tuples)
	"""

	coordTrans = osr.CoordinateTransformation(source_srs, target_srs)

	line = ogr.Geometry(ogr.wkbLineString)
	line.AssignSpatialReference(source_srs)
	has_elevation = False
	if len(coord_list[0]) > 2:
		has_elevation = True
	for coord in coord_list:
		x, y = coord[:2]
		if has_elevation:
			z = coord[2]
			line.AddPoint(x, y, z)
		else:
			line.AddPoint(x, y)
	line.Transform(coordTrans)
	out_coord_list = []
	for i in range(line.GetPointCount()):
		if has_elevation:
			out_coord_list.append((line.GetX(i), line.GetY(i), line.GetZ(i)))
		else:
			out_coord_list.append((line.GetX(i), line.GetY(i)))
	line.Empty()
	return out_coord_list


def gen_transform_coordinates(source_srs, target_srs, coord_list):
	"""
	Transform (reproject) a list of coordinates one by one
	(to avoid memory problems).

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param coord_list:
		List of (lon, lat, [z]) or (easting, northing, [z]) tuples

	:return:
		Generator yielding (x, y, [z]) tuple of transformed coordinates
	"""

	ct = osr.CoordinateTransformation(source_srs, target_srs)
	has_elevation = False
	if len(coord_list[0]) > 2:
		has_elevation = True

	for coord in coord_list:
		x, y = coord[:2]
		if has_elevation:
			z = coord[2]
			yield ct.TransformPoint(x, y, z)
		else:
			yield ct.TransformPoint(x, y)[:2]


def transform_array_coordinates(source_srs, target_srs, x_source, y_source, z_source=None):
	"""
	Transform (reproject) coordinates in separate arrays

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param x_source:
		1-D float array, input coordinate array representing x coordinates
		(longitudes or eastings) of a meshed grid
	:param y_source:
		1-D float array, input coordinate array representing y coordinates
		(latitudes or northings) of a meshed grid
	:param z_source:
		1-D float array, input coordinate array representing z coordinates
		(default: None)

	:return:
		(x, y, [z]) tuple of 1-D float arrays: output coordinate arrays
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

	if z_source is None or len(z_source) == 0:
		has_elevation = False
		xyz_source = np.column_stack([x_source, y_source])
	else:
		has_elevation = True
		xyz_source = np.column_stack([x_source, y_source, z_source])

	xyz_target = np.array(ct.TransformPoints(xyz_source)).T

	if has_elevation:
		return xyz_target[0], xyz_target[1], xyz_target[2]
	else:
		return xyz_target[0], xyz_target[1]


def transform_mesh_coordinates(source_srs, target_srs, x_source, y_source):
	"""
	Transform (reproject) meshed coordinates
	Source: http://stackoverflow.com/questions/20488765/plot-gdal-raster-using-matplotlib-basemap

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param x_source:
		2-D float array, input coordinate array representing x coordinates
		(longitudes or eastings) of a meshed grid
	:param y_source:
		2-D float array, input coordinate array representing y coordinates
		(latitudes or northings) of a meshed grid

	:return:
		(xx, yy) tuple of 2-D float arrays: output coordinate arrays
		representing x and y coordinates of a meshed grid
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

	## the ct object takes and returns pairs of x,y, not 2d grids
	## so the the grid needs to be reshaped (flattened) and back.
	size = x_source.size
	shape = x_source.shape
	xy_source = np.zeros((size, 2))
	xy_source[:,0] = x_source.reshape(1, size)
	xy_source[:,1] = y_source.reshape(1, size)

	xy_target = np.array(ct.TransformPoints(xy_source))

	xx = xy_target[:,0].reshape(shape)
	yy = xy_target[:,1].reshape(shape)

	return xx, yy


def lonlat_to_lambert1972(coord_list):
	"""
	Convert geographic coordinates (WGS84) to Lambert 1972

	:param coord_list:
		List of (lon, lat) tuples

	:return:
		List of (easting, northing) tuples
	"""
	return transform_coordinates(wgs84, lambert1972, coord_list)


def lambert1972_to_lonlat(coord_list):
	"""
	Convert Lambert 1972 coordinates to geographic coordinates (WGS84)

	:param coord_list:
		List of (easting, northing) tuples

	:return:
		List of (lon, lat) tuples
	"""
	return transform_coordinates(lambert1972, wgs84, coord_list)


def lonlat_to_utm(coord_list, utm_spec="UTM31N"):
	"""
	Convert geographic coordinates (WGS84) to Lambert 1972

	:param coord_list:
		List of (lon, lat) tuples
	:param utm_spec:
		String, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")

	:return:
		List of (easting, northing) tuples
	"""
	utm_srs = get_utm_srs(utm_spec)
	return transform_coordinates(wgs84, utm_srs, coord_list)


def utm_to_lonlat(coord_list, utm_spec="UTM31N"):
	"""
	Convert Lambert 1972 coordinates to geographic coordinates (WGS84)

	:param coord_list:
		List of (easting, northing) tuples
	:param utm_spec:
		String, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")

	:return:
		List of (lon, lat) tuples
	"""
	utm_srs = get_utm_srs(utm_spec)
	return transform_coordinates(utm_srs, wgs84, coord_list)


def lonlat_to_ECEF(coord_list, a=1., e=0.):
	"""
	Convert geographic coordinates to earth-centered, earth-fixed coordinates

	:param coord_list:
		List of (easting, northing, altitude) tuples
		altitude in meters
	:param a:
		Float, semi-major axis of ellipsoid (default: 1.)
	:param e:
		Float, eccentricity of ellipsoid (default: 0.)

	:return:
		List of (X, Y, Z) tuples
	"""
	def get_prime_vertical_of_curvature(phi, a, e):
		## return prime vertical of curvature (in meters)
		return a / np.sqrt(1. - np.e**2 * (np.sin(phi))**2)

	lons, lats, h = zip(*coord_list)
	lamda = np.radians(lons)
	phi = np.radians(lats)
	N = get_prime_vertical_of_curvature(phi, a, e)

	X = (N + h) * np.cos(phi) * np.cos(lamda)
	Y = (N + h) * np.cos(phi) * np.sin(lamda)
	Z = (N * (1. - np.e**2) + h) * np.sin(phi)

	return (X, Y, Z)


def lonlat_to_ECEF2(coord_list):
	"""
	Convert geographic coordinates to earth-centered, earth-fixed coordinates

	:param coord_list:
		List of (easting, northing, altitude) tuples
		altitude in meters

	:return:
		List of (X, Y, Z) tuples
	"""
	ecef_wkt = """
	GEOCCS['WGS 84',
	DATUM['WGS_1984',
		SPHEROID['WGS 84',6378137,298.257223563,
			AUTHORITY['EPSG','7030']],
		AUTHORITY['EPSG','6326']],
	PRIMEM['Greenwich',0,
		AUTHORITY['EPSG','8901']],
	UNIT['metre',1,
		AUTHORITY['EPSG','9001']],
	AXIS['Geocentric X',OTHER],
	AXIS['Geocentric Y',OTHER],
	AXIS['Geocentric Z',NORTH],
	AUTHORITY['EPSG','4978']]
	"""
	ecef = osr.SpatialReference()
	ecef.ImportFromWkt(ecef_wkt)
	return transform_coordinates(wgs84, ecef, coord_list)


def wkt2epsg(wkt, tolerance=1E-05):
	"""
	Transform a WKT string to an EPSG code
	Modified from: http://gis.stackexchange.com/questions/20298/is-it-possible-to-get-the-epsg-value-from-an-osr-spatialreference-class-using-th

	:param wkt:
		str, WKT definition
	:param tolerance:
		float, tolerance to accept projection parameters as equal

	:return:
		int, EPSG code
	"""

	import os
	import numpy as np
	import pyproj
	import osr

	epsg = os.path.join(pyproj.pyproj_datadir, "epsg")

	def proj_string_to_dict(proj_str):
		"""
		Convert proj string to a dictionary
		"""
		fields = proj_str.split()
		proj_dict = {}
		for f in fields:
			if not '<>' in f:
				try:
					key, val = f.split('=')
				except:
					key, val = f, None
				else:
					try:
						val = int(val)
					except:
						try:
							val = float(val)
						except:
							pass
				proj_dict[key] = val
		return proj_dict

	def match_proj_dicts(proj_dict1, proj_dict2, general_keys_only=False):
		"""
		Match 2 proj dictionaries. We only take into account parameters
		from the 2nd argument.

		:return:
			bool, whether or not there is a match
		"""
		general_keys = ['+proj', '+ellps', '+units']
		for key in general_keys:
			if proj_dict1.get(key) != proj_dict2.get(key):
				return False
		if general_keys_only:
			return True

		other_keys = set(proj_dict2.keys()).difference(set(general_keys))
		for key in other_keys:
			val1, val2 = proj_dict1.get(key), proj_dict2.get(key)
			if isinstance(val1, (int, float)):
				if not np.allclose(val1, val2 ,atol=tolerance):
					return False
			else:
				if val1 != val2:
					return False
		return True

	code = None
	p_in = osr.SpatialReference()
	s = p_in.ImportFromWkt(wkt)
	if s == 5:  # invalid WKT
		return None
	if p_in.IsLocal() == 1:  # this is a local definition
		return p_in.ExportToWkt()
	if p_in.IsGeographic() == 1:  # this is a geographic srs
		cstype = 'GEOGCS'
	else:  # this is a projected srs
		cstype = 'PROJCS'
	p_in.AutoIdentifyEPSG()
	an = p_in.GetAuthorityName(cstype)
	ac = p_in.GetAuthorityCode(cstype)
	if an == 'EPSG' and ac is not None:  # return the EPSG code
		return ac

	else:
		## try brute force approach by grokking proj epsg definition file
		from collections import OrderedDict
		p_out = p_in.ExportToProj4()
		if p_out:
			proj_epsg = OrderedDict()
			with open(epsg) as f:
				for line in f:
					try:
						code, proj_str = line.split('>', 1)
					except:
						pass
					else:
						code = int(code[1:])
						if proj_str.find(p_out) != -1:
							## Literal match
							return code
						proj_dict = proj_string_to_dict(proj_str.strip())
						proj_epsg[code] = proj_dict

			p_out_dict = proj_string_to_dict(p_out)
			for code, proj_dict in proj_epsg.items():
				match = match_proj_dicts(proj_dict, p_out_dict)
				if not match:
					## Try swapping standard parallels
					if match_proj_dicts(proj_dict, p_out_dict, general_keys_only=True):
						try:
							lat1, lat2 = p_out_dict['+lat_1'], p_out_dict['+lat_2']
						except:
							pass
						else:
							p_out_dict['+lat_1'] = lat2
							p_out_dict['+lat_2'] = lat1
							match = match_proj_dicts(proj_dict, p_out_dict)
				if match:
					return code


if __name__ == "__main__":
	## Should return 66333.00 222966.00
	coord_list = [(3.1688526555555554, 51.31044484722222)]
	print "%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0]

	## Should return 226696.00 203425.00
	coord_list = [(5.464567200000001, 51.135779408333335)]
	print "%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0]

	## Should return 127514.00 132032.00
	coord_list = [(4.051806319444444, 50.49865343055556)]
	print "%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0]

	## Should return -2430880.68434096 -4770871.96871711 3453958.6411779
	coord_list = [(-117, 33, 0)]
	print lonlat_to_ECEF2(coord_list)
