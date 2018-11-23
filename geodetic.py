"""
Distance/azimuth calculations in cartesian and spherical coordinate systems
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import numpy as np


## Earth's radius in km
EARTH_RADIUS = 6371.


def cartesian_distance(x1, y1, x2, y2):
	"""
	Compute distance between two points in cartesian coordinates.

	:param x1:
		float or numpy array, x coordinate(s) of point(s) A (origin)
	:param y1:
		float or numpy array, y coordinate(s) of point(s) A (origin)
	:param x2:
		float or numpy array, x coordinate(s) of point(s) B (destination)
	:param y2:
		float or numpy array, y coordinate(s) of point(s) B (destination)

	:return:
		float or numpy array, distance in same units as input coordinates
	"""
	return np.sqrt((x1-x2)**2 + (y1-y2)**2)


def spherical_distance(lon1, lat1, lon2, lat2):
	"""
	Compute distance between two points using the haversine formula.
	Modified from: http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/

	:param lon1:
		float or numpy array, longitude(s) of point(s) A in decimal degrees
	:param lat1:
		float or numpy array, latitude(s) of point(s) A in decimal degrees
	:param lon1:
		float or numpy array, longitude(s) of point(s) B in decimal degrees
	:param lat1:
		float or numpy array, latitude(s) of point(s) B in decimal degrees

	:return:
		float or numpy array, distance in m
	"""
	dlat = np.radians(lat2 - lat1)
	dlon = np.radians(lon2 - lon1)
	a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
		* np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
	c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
	d = EARTH_RADIUS * c
	return d * 1000.


def cartesian_azimuth(x1, y1, x2, y2):
	"""
	Compute azimuth between two points in cartesian coordinates.

	:param x1:
		float or numpy array, x coordinate(s) of point(s) A
	:param y1:
		float or numpy array, y coordinate(s) of point(s) A
	:param x2:
		float or numpy array, x coordinate(s) of point(s) B
	:param y2:
		float or numpy array, y coordinate(s) of point(s) B

	:return:
		float or numpy array, azimuth in degrees
	"""
	angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
	bearing = (90 - angle) % 360
	return bearing


def spherical_azimuth(lon1, lat1, lon2, lat2):
	"""
	Calculate the compass bearing between two points.
	Modified from: https://gist.github.com/2005586

	:param lon1:
		float or numpy array: longitude(s) of point(s) A in decimal degrees
	:param lat1:
		float or numpy array: latitude(s) of point(s) A in decimal degrees
	:param lon1:
		float or numpy array: longitude(s) of point(s) B in decimal degrees
	:param lat1:
		float or numpy array: latitude(s) of point(s) B in decimal degrees

	:return:
		float or numpy array, compass bearing in degrees
	"""
	lat1 = np.radians(lat1)
	lat2 = np.radians(lat2)
	dlon = np.radians(lon2 - lon1)

	x = np.sin(dlon) * np.cos(lat2)
	y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(dlon))
	initial_bearing = np.arctan2(x, y)

	# Now we have the initial bearing but np.arctan2 returns values
	# from -180 to + 180 degrees which is not what we want for a compass bearing
	# The solution is to normalize the initial bearing as shown below
	initial_bearing = np.degrees(initial_bearing)
	compass_bearing = (initial_bearing + 360) % 360
	return compass_bearing


def cartesian_point_at(x1, y1, distance, azimuth):
	"""
	Compute coordinates of point at given distance and azimuth
	from origin in cartesian coordinates.
	Note: only one of (x1, y1), distance or azimuth may be a
	numpy array. If one is an array, the others must be floats.

	:param x1:
		float or numpy array, X coordinate(s) of origin
	:param y1:
		float or numpy array, Y coordinate(s) of origin
	:param distance:
		float or numpy array, distance in same units as input coordinates
	:param azimuth:
		float or numpy array, azimuth in degrees

	:return:
		tuple (x2, y2) of floats or numpy arrays containing
		X and Y coordinates of point(s)
	"""
	azimuth = np.radians(azimuth)
	x2 = x1 + distance * np.sin(azimuth)
	y2 = y1 + distance * np.cos(azimuth)
	return (x2, y2)


def spherical_point_at(lon1, lat1, distance, azimuth):
	"""
	Compute coordinates of point at given distance and azimuth
	from origin in spherical coordinates.
	Note: only one of (lon1, lat1), distance or azimuth may be a
	numpy array. If one is an array, the others must be floats.

	:param lon1:
		float or numpy array, longitude(s) of origin in degrees
	:param lat1:
		float or numpy array, latitude(s) of origin in degrees
	:param distance:
		float or numpy array, distance in m
	:param azimuth:
		float or numpy array, azimuth in degrees

	:return:
		tuple (lon2, lat2) of floats or numpy arrays containing
		longitude(s) and latitude(s) of point(s)
	"""
	lon1, lat1 = np.radians(lon1), np.radians(lat1)
	azimuth = np.radians(azimuth)
	half_pi = np.pi / 2

	b = distance / (EARTH_RADIUS * 1000)
	sin_b = np.sin(b)
	a = np.arccos(np.cos(b) * np.cos(half_pi-lat1) + np.sin(half_pi-lat1) * sin_b * np.cos(azimuth))
	B = np.arcsin(sin_b * np.sin(azimuth) / np.sin(a))
	lat2 = 90 - np.degrees(a)
	lon2 = np.degrees(lon1 + B)
	return (lon2, lat2)
