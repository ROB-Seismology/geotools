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


def transform_coordinates(source_srs, target_srs, coord_list):
	"""
	Transform (reproject) source and receiver coordinates.
	Header words sx, sy, gx, gy, counit, and scalco are modified in-place.

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

