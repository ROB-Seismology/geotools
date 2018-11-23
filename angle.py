"""
Some numeric operations (mean, difference) on geographic angles or azimuths
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import numpy as np


def mean_angle(angles, weights=None):
	"""
	Compute weighted mean geographic angle
	Modified from: http://positivelyglorious.com/software-media/averages-of-azimuths/

	:param angles:
		list or numpy array with angles in degrees
	:param weights:
		list or numpy array with weights (default: None)

	:return:
		float, mean angle in degrees
	"""
	rad_angles = np.radians(angles)
	## Mean Y component
	sa = np.average(np.sin(rad_angles), weights=weights)
	## Mean X component
	ca = np.average(np.cos(rad_angles), weights=weights)
	## Take the arctan of the averages, and convert to degrees
	mean_angle = np.degrees(np.arctan2(sa, ca))
	return mean_angle


def constrain_azimuth(azimuths):
	"""
	Constrain azimuths to the range [0, 360]

	:param azimuths:
		float, list or numpy array, geographic angles (in degrees)

	:return:
		float or array, azimuths
	"""
	return (np.asarray(azimuths) + 360) % 360


def mean_azimuth(azimuths, weights=None):
	"""
	Compute weighted mean azimuth

	:param azimuths:
		list or numpy array, azimuths in degrees
	:param weights:
		list or numpy array, corresponding weights (default: None)

	:return:
		float, mean azimuth in degrees
	"""
	mean_azimuth = mean_angle(azimuths, weights=weights)
	mean_azimuth = constrain_azimuth(mean_azimuth)
	return mean_azimuth


def delta_angle(angle1, angle2):
	"""
	Compute difference between two geographic angles or azimuths

	:param angle1:
		float, list or array, first angle in degrees
	:param angle2:
		float, list or array, second angle in degrees

	:return:
		float or array, angle difference in degrees
	"""
	## Convert angles to unit vectors
	rad_angle1 = np.radians(angle1)
	rad_angle2 = np.radians(angle2)
	v1_x, v1_y = np.cos(rad_angle1), np.sin(rad_angle1)
	v2_x, v2_y = np.cos(rad_angle2), np.sin(rad_angle2)
	v1, v2 = np.array([v1_x, v1_y]), np.array([v2_x, v2_y])

	rad_delta = np.arccos(np.dot(v1, v2))

	## This should be equivalent
	#rad_delta = np.arctan2(v2_y, v2_x) - np.arctan2(v1_y, v1_x)

	if np.isnan(rad_delta):
		if (v1 == v2).all():
			rad_delta = 0.0
		else:
			rad_delta = np.pi

	return np.degrees(rad_delta)
