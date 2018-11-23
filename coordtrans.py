"""
Transformation of coordinates between different spatial reference systems
"""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
	## Python 2
	basestring
except:
	## Python 3
	basestring = str


import os
import numpy as np
import ogr
import osr



## Some useful spatial reference systems

## WGS84
WGS84 = osr.SpatialReference()
WGS84_EPSG = 4326
WGS84.ImportFromEPSG(WGS84_EPSG)

## Lambert 1972
## WKT corresponding to MapInfo specification
LAMBERT1972_WKT = ('PROJCS["Belgian National System (7 parameters)",'
				'GEOGCS["unnamed",DATUM["Belgian 1972 7 Parameter",'
				'SPHEROID["International 1924",6378388,297],'
				'TOWGS84[-99.059,53.322,-112.486,0.419,-0.83,1.885,0.999999]],'
				'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
				'PROJECTION["Lambert_Conformal_Conic_2SP"],'
				'PARAMETER["standard_parallel_1",49.8333339],'
				'PARAMETER["standard_parallel_2",51.1666672333],'
				'PARAMETER["latitude_of_origin",90],'
				'PARAMETER["central_meridian",4.3674866667],'
				'PARAMETER["false_easting",150000.013],'
				'PARAMETER["false_northing",5400088.438],UNIT["Meter",1.0]]')
LAMBERT1972 = osr.SpatialReference()
#LAMBERT1972.ImportFromWkt(LAMBERT1972_WKT)
#LAMBERT1972_EPSG = 31370
## EPSG code for Belgian Lambert 72 + Ostend height
## (less than 10 cm difference with SRS based on WKT)
LAMBERT1972_EPSG = 6190
LAMBERT1972.ImportFromEPSG(LAMBERT1972_EPSG)

## ECEF: Earth centred, earth fixed, righthanded 3D coordinate system
ECEF_WKT = """
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
ECEF_EPSG = 4978
ECEF = osr.SpatialReference()
ECEF.ImportFromEPSG(ECEF_EPSG)


def get_epsg_srs(epsg_code):
	"""
	Get spatial reference from EPSG code

	:param epsg_code:
		str or int, EPSG code (e.g., "EPSG:3857", "3857" or 3857)

	:return:
		Instance of :class:`osr.SpatialReference`
	"""
	if isinstance(epsg_code, basestring):
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
		float, longitude (in degrees)
	:param lat:
		float, latitude (in degrees)

	:return:
		(int, str) tuple: UTM zone, hemisphere
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
		str, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")
		or
		(int, str) tuple with UTM zone and hemisphere

	:return:
		Instance of :class:`osr.SpatialReference`
	"""
	if not isinstance(utm_spec, basestring):
		utm_zone, hemisphere = utm_spec[:2]
		utm_spec = "UTM%d%s" % (utm_zone, hemisphere)
	utm_hemisphere = utm_spec[-1]
	utm_zone = int(utm_spec[-3:-1])
	utm = osr.SpatialReference()
	utm.SetProjCS("UTM %d (WGS84) in northern hemisphere." % utm_zone)
	#utm.SetWellKnownGeogCS("WGS84")
	utm.ImportFromEPSG()
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
		list of (lon, lat, [z]) or (easting, northing, [z]) tuples

	:return:
		list of transformed coordinates (tuples)
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

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
	line.Transform(ct)
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
		list of (lon, lat, [z]) or (easting, northing, [z]) tuples

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


def transform_array_coordinates(source_srs, target_srs, X, Y, Z=None):
	"""
	Transform (reproject) coordinates in separate arrays

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param X:
		1-D float array, input coordinate array representing x coordinates
		(longitudes or eastings) of a meshed grid
	:param Y:
		1-D float array, input coordinate array representing y coordinates
		(latitudes or northings) of a meshed grid
	:param Z:
		1-D float array, input coordinate array representing z coordinates
		(default: None)

	:return:
		(x, y, [z]) tuple of 1-D float arrays: output coordinate arrays
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

	if Z is None or len(Z) == 0:
		has_elevation = False
		xyz_source = np.column_stack([X, Y])
	else:
		has_elevation = True
		xyz_source = np.column_stack([X, Y, Z])

	xyz_target = np.array(ct.TransformPoints(xyz_source)).T

	if has_elevation:
		return xyz_target[0], xyz_target[1], xyz_target[2]
	else:
		return xyz_target[0], xyz_target[1]


def transform_mesh_coordinates(source_srs, target_srs, XX, YY):
	"""
	Transform (reproject) meshed coordinates
	Source: http://stackoverflow.com/questions/20488765/plot-gdal-raster-using-matplotlib-basemap

	:param source_srs:
		osr SpatialReference object: source coordinate system
	:param target_srs:
		osr SpatialReference object: target coordinate system
	:param XX:
		2-D float array, input coordinate array representing x coordinates
		(longitudes or eastings) of a meshed grid
	:param YY:
		2-D float array, input coordinate array representing y coordinates
		(latitudes or northings) of a meshed grid

	:return:
		(xx, yy) tuple of 2-D float arrays: output coordinate arrays
		representing x and y coordinates of a meshed grid
	"""
	ct = osr.CoordinateTransformation(source_srs, target_srs)

	## the ct object takes and returns pairs of x,y, not 2d grids
	## so the the grid needs to be reshaped (flattened) and back.
	size = XX.size
	shape = XX.shape
	xy_source = np.zeros((size, 2))
	xy_source[:,0] = XX.reshape(1, size)
	xy_source[:,1] = YY.reshape(1, size)

	xy_target = np.array(ct.TransformPoints(xy_source))

	xx = xy_target[:,0].reshape(shape)
	yy = xy_target[:,1].reshape(shape)

	return xx, yy


def lonlat_to_lambert1972(lons, lats=None, z=None):
	"""
	Convert geographic coordinates (WGS84) to Lambert 1972

	:param lons:
		list or 1-D array, longitudes (in degrees)
		or list of (lon, lat, [z]) tuples
	:param lats:
		list or 1-D array, latitudes (in degrees)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)

	:return:
		tuple of (X, Y, [Z]) arrays
		or list of (easting, northing, [z]) tuples (in meters)
	"""
	if lats is None:
		coords = lons
		return transform_coordinates(WGS84, LAMBERT1972, coords)
	else:
		return transform_array_coordinates(WGS84, LAMBERT1972, lons, lats, z)


def lambert1972_to_lonlat(x, y=None, z=None):
	"""
	Convert Lambert 1972 coordinates to geographic coordinates (WGS84)

	:param x:
		list or 1-D array, eastings
		or list of (x, y, [z]) tuples (in meters)
	:param y:
		list or 1-D array, northings (in meters)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)

	:return:
		tuple of (lons, lats, [Z]) arrays
		or list of (lon, lat, [z]) tuples
	"""
	if y is None:
		coords = x
		return transform_coordinates(LAMBERT1972, WGS84, coords)
	else:
		return transform_array_coordinates(LAMBERT1972, WGS84, x, y, z)


def lonlat_to_utm(lons, lats=None, z=None, utm_spec="UTM31N"):
	"""
	Convert geographic coordinates (WGS84) to Lambert 1972

	:param lons:
		list or 1-D array, longitudes (in degrees)
		or list of (lon, lat, [z]) tuples
	:param lats:
		list or 1-D array, latitudes (in degrees)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)
	:param utm_spec:
		String, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")

	:return:
		tuple of (X, Y, [Z]) arrays
		or list of (easting, northing, [z]) tuples (in meters)
	"""
	utm_srs = get_utm_srs(utm_spec)
	if lats is None:
		coords = lons
		return transform_coordinates(WGS84, utm_srs, coords)
	else:
		return transform_array_coordinates(WGS84, utm_srs, lons, lats, z)


def utm_to_lonlat(x, y=None, z=None, utm_spec="UTM31N"):
	"""
	Convert Lambert 1972 coordinates to geographic coordinates (WGS84)

	:param x:
		list or 1-D array, eastings
		or list of (x, y, [z]) tuples (in meters)
	:param y:
		list or 1-D array, northings (in meters)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)
	:param utm_spec:
		String, UTM specification: "UTM" + "%02d" % zone_number + "%c" % hemisphere
		(default: "UTM31N")

	:return:
		tuple of (lons, lats, [Z]) arrays
		or list of (lon, lat, [z]) tuples
	"""
	utm_srs = get_utm_srs(utm_spec)
	if y is None:
		coords = x
		return transform_coordinates(utm_srs, WGS84, coords)
	else:
		return transform_array_coordinates(utm_srs, WGS84, x, y, z)


def lonlat_to_meter(lons, lats, ref_lat=None, ellipsoidal=True):
	"""
	Convert geographic coordinates to meters, useful to approximate
	short distances

	See: https://en.wikipedia.org/wiki/Geographic_coordinate_system#Expressing_latitude_and_longitude_as_linear_units

	:param lons:
		array, longitudes (in degrees)
	:param lats:
		array, latitudes (in degrees)
	:param ref_lat:
		float, reference latitude (in degrees)
		(default: None, will use mean of :param:`lats`)
	:param ellipsoidal:
		bool, whether to use ellipsoidal (WGS84) of spherical
		Earth approximation
		(default: True)

	:return:
		tuple of (X, Y) arrays (in meters)
	"""
	if ref_lat is None:
		ref_lat = np.mean(lats)
	ref_lat = np.radians(ref_lat)

	if not ellipsoidal:
		## Spherical
		m_per_deg_lat = 111133.84012073894
		m_per_deg_lon = m_per_deg_lat * np.cos(ref_lat)

	else:
		## WGS84, accurate within a centimeter
		m_per_deg_lat = (111132.92 - 559.82 * np.cos(ref_lat * 2)
				+ 1.175 * np.cos(ref_lat * 4) - 0.0023 * np.cos(ref_lat * 6))
		m_per_deg_lon = (111412.84 * np.cos(ref_lat) - 93.5 * np.cos(ref_lat * 3)
				+ 0.118 * np.cos(ref_lat * 5))

	x = lons * m_per_deg_lon
	y = lats * m_per_deg_lat

	return (x, y)


def lonlat_to_ECEF2(lons, lats=None, z=None, a=1., e=0.):
	"""
	Convert geographic coordinates to earth-centered, earth-fixed coordinates
	See: https://gssc.esa.int/navipedia/index.php/Ellipsoidal_and_Cartesian_Coordinates_Conversion

	:param lons:
		list or 1-D array, longitudes (in degrees)
		or list of (lon, lat, z) tuples
	:param lats:
		list or 1-D array, latitudes (in degrees)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)
	:param a:
		float, semi-major axis of ellipsoid (default: 1.)
	:param e:
		float, eccentricity of ellipsoid (default: 0.)

	:return:
		tuple of (X, Y, Z) arrays
		or list of (easting, northing, z) tuples (in meters)
	"""
	def get_curvature_radius_of_prime_vertical(phi, a, e):
		## return radius of curvature in the prime vertical (in meters)
		return a / np.sqrt(1. - e**2 * (np.sin(phi))**2)

	if lats is None:
		coords = lons
		lons, lats, z = zip(*coords)
	lamda = np.radians(lons)
	phi = np.radians(lats)
	z = np.asarray(z)
	N = get_curvature_radius_of_prime_vertical(phi, a, e)

	X = (N + z) * np.cos(phi) * np.cos(lamda)
	Y = (N + z) * np.cos(phi) * np.sin(lamda)
	Z = (N * (1. - e**2) + z) * np.sin(phi)

	return (X, Y, Z)


def lonlat_to_ECEF(lons, lats=None, z=None):
	"""
	Convert geographic coordinates to earth-centered, earth-fixed coordinate
	system, consisting of 3 orthogonal axes with X and Y axes in the equatorial
	plane, positive Z-axis parallel to mean earth rotation axis and
	pointing towards North Pole

	:param lons:
		list or 1-D array, longitudes (in degrees)
		or list of (lon, lat, z) tuples
	:param lats:
		list or 1-D array, latitudes (in degrees)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)

	:return:
		tuple of (X, Y, Z) arrays
		or list of (easting, northing, z) tuples (in meters)
	"""
	if lats is None:
		coords = lons
		return transform_coordinates(WGS84, ECEF, coords)
	else:
		return transform_array_coordinates(WGS84, ECEF, lons, lats, z)


def ECEF_to_lonlat(x, y=None, z=None):
	"""
	Convert earth-centered, earth-fixed coordinates to geographic coordinates.

	:param x:
		list or 1-D array, eastings (in meters)
		or list of (lon, lat, z) tuples
	:param y:
		list or 1-D array, northings (in meters)
		(default: None)
	:param z:
		list or 1-D array, altitudes (in meters)
		(default: None)

	:return:
		tuple of (lons, lats, Z) arrays
		or list of (lon, lat, z) tuples (in degrees)
	"""
	if y is None:
		coords = x
		return transform_coordinates(ECEF, WGS84, coords)
	else:
		return transform_array_coordinates(ECEF, WGS84, x, y, z)


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
	import pyproj

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
	print("%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0])

	## Should return 226696.00 203425.00
	coord_list = [(5.464567200000001, 51.135779408333335)]
	print("%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0])

	## Should return 127514.00 132032.00
	coord_list = [(4.051806319444444, 50.49865343055556)]
	print("%.2f, %.2f" % lonlat_to_lambert1972(coord_list)[0])

	## Should return -2430880.68434096 -4770871.96871711 3453958.6411779
	coord_list = [(-117, 33, 0)]
	print(lonlat_to_ECEF(coord_list))
	print(lonlat_to_ECEF2(coord_list))
