"""
Module Angle

This module provides the class Angle, for dealing with mathematical angles,
and the derived class Azimuth, for dealing with geographic angles.
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import numpy as np


__all__ = ['Angle', 'Azimuth', 'acos', 'asin', 'atan', 'atan2']



class Angle:
	"""
	Class Angle implements a special object for angles.
	Angles are measured counterclockwise from the positive X-axis.
	Angle objects are constrained to the domain (-pi, +pi), but otherwise
	behave like normal floats or float arrays, with additional methods
	for angle type conversion.

	Angle objects are created by specifying a value and an optional parameter
	specifying the format of the value:
		a = Angle(val, [[format=]"rad"/"deg"/"gon"/"mil"/"dms"/"dm"])
	The value passed in is automatically converted to radians.

	The following methods are provided:
	- deg2rad(), gon2rad(), mil2rad(), dms2rad() and dm2rad():
		these are implemented as static functions that can be called without
		needing to create a class instance;
		they take a numeric value or tuple and return corresponding angle in
		radians as a float;
	- rad(), deg(), gon(), mil(), dms() and dm():
		these methods don't take any argument, and simply return the angle
		as radians, degrees, gons, mils (as a float), dms or dm (as a tuple);
	- constrain360() and constrain180():
		these methods don't take any argument, and constrain the angle object
		to the domains (0, 2*np.pi) and (-np.pi, +np.pi), respectively
		(value is changed in place);
	- get_complement(), get_supplement() and get_reverse():
		don't take any argument, return new angle object that is complementary,
		supplementary, resp. reverse of the current angle object;
	- to_azimuth():
		doesn't take any argument, converts mathematical angle to geographical
		azimuth, and returns it as a new object of type Azimuth (derived from Angle).
	"""
	def __init__(self, val, format="rad"):
		if isinstance(val, list):
			val = np.array(val)

		## Dispatch conversion using dictionary
		self.__val = { "rad": self.__rad2rad,
			"deg": self.deg2rad,
			"gon": self.gon2rad,
			"mil": self.mil2rad,
			"dms": self.dms2rad,
			"dm": self.dm2rad}[format](val)

		## We store the angle value as radians in self.__val,
		## which is a float and is hidden to the outside world

		## By default, we constrain the angle to the domain (-np.pi, +np.pi)
		self.constrain180()

	## The following methods help distinguishing between Angle and Azimuth

	def is_angle(self):
		return True

	def is_azimuth(self):
		return False

	def is_other_angle_type(self, other):
		"""
		Determine whether given object is another angle type
		(requiring conversion before some operation is applied)

		:param other:
			any object type
		:return:
			bool
		"""
		if not isinstance(other, Angle):
			return False
		elif isinstance(other, Azimuth) and not isinstance(self, Azimuth):
			return True
		elif isinstance(self, Azimuth) and not isinstance(other, Azimuth):
			return True

	def isscalar(self):
		"""
		Indicate whether instance is scalar (True) or array (False)
		"""
		return np.isscalar(self.__val)

	## The following methods make non-scalar instances behave like arrays

	def __getitem__(self, item):
		try:
			return self.__class__(self.__val.__getitem__(item))
		except TypeError:
			raise TypeError("%s instance is scalar and does not support slicing/indexing" % self.__class__)

	def __len__(self):
		try:
			return len(self.__val)
		except TypeError:
			raise TypeError("%s instance is scalar and has no length" % self.__class__)

	## The following methods overload operators, so that angles behave as
	## normal floats or float arrays

	def __coerce__(self, other):
		"""
		This method is called when other overload methods are called,
		so it is not necessary to convert Azimuths to Angles (or vice
		versa) in each method separately
		"""
		if self.is_other_angle_type(other):
			other = other.to_other_angle_type()
		return (self, other)

	def __add__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(self.__val + other.__float__())

	def __sub__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(self.__val - other.__float__())

	def __mul__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(self.__val * other.__float__())

	def __div__(self, other):
		return self.__truediv__(other)

	def __truediv__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(self.__val / other.__float__())

	def __floordiv__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(self.__val // other.__float__())

	def __pow__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(np.power(self.__val, other.__float__()))

	def __mod__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(np.remainder(self.__val, other.__float__()))

	def __divmod__(self, other):
		"""
		Note: only remainder is returned as Angle/Azimuth object
		"""
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		#div, mod = np.divmod(self.__val, other.__float__())
		#return (div, mod)
		div, mod = self.__val.__divmod__(other.__float__())
		return (div, self.__class__(mod))

	## __r__ functions are necessary for non-Angle objects

	def __radd__(self, other):
		return self.__add__(other)

	def __rsub__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(other.__float__() - self.__val)

	def __rmul__(self, other):
		return self.__mul__(other)

	def __rdiv__(self, other):
		return self.__rtruediv__(other)

	def __rtruediv__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(other.__float__() / self.__val)

	def __rfloordiv__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(other.__float__() // self.__val)

	def __rpow__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(np.power(other.__float__(), self.__val))

	def __rmod__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		return self.__class__(np.remainder(other.__float__(), self.__val))

	def __rdivmod__(self, other):
		#if self.is_other_angle_type(other):
		#	other = other.to_other_angle_type()
		div, mod = np.divmod(other.__float__(), self.__val)
		return (div, self.__class__(mod))

	def __abs__(self):
		return self.__class__(np.abs(self.__val))

	def __neg__(self):
		return self.__class__(-self.__val)

	def __pos__(self):
		return self.__class__(+self.__val)

	def __float__(self):
		return self.__val

	def __int__(self):
		return np.int64(self.__val)
		#return int(self.__val)

	#def __long__(self):
	#	return long(self.__val)

	def __eq__(self, other):
		if self.is_other_angle_type(other):
			## Should always return False
			return np.isinf(self.__val)
		else:
			return np.isclose(self.__val, other.__float__())

	def __ne__(self, other):
		if self.is_other_angle_type(other):
			## Should always return True
			return np.isfinite(self.__val)
		else:
			return np.logical_not(np.isclose(self.__val, other.__float__()))

	## Comparison functions for scalar instances (not sure this is still required)

	def __cmp__(self, other):
		"""
		Comparison if scalar
		"""
		if self.is_other_angle_type(other):
			raise TypeError
		return np.sign(self.__val - other.__float__())

	## Comparison functions for non-scalar instances

	def __gt__(self, other):
		if self.is_other_angle_type(other):
			raise TypeError
		return self.__val.__gt__(other.__float__())

	def __ge__(self, other):
		if self.is_other_angle_type(other):
			raise TypeError
		return self.__val.__ge__(other.__float__())

	def __lt__(self, other):
		if self.is_other_angle_type(other):
			raise TypeError
		return self.__val.__lt__(other.__float__())

	def __le__(self, other):
		if self.is_other_angle_type(other):
			raise TypeError
		return self.__val.__le__(other.__float__())

	def __nonzero__(self):
		"""
		Called in if statement where instance is the condition, e.g.
		a = Angle(0)
		if a:
			...
		"""
		try:
			return self.__val.__nonzero__()
		except:
			return int(self.__val.any())

	def __repr__(self):
		return repr(self.__val) + " rad"

	def __str__(self):
		return str(self.__val)

	## The following methods convert various angle formats into radians
	## They return floats and are implemented as static methods
	## (except for rad2rad(), which is of no general use and remains hidden

	def __rad2rad(self, angle):
		""" Convert angle in radians into a float """
		return angle * 1.0

	@staticmethod
	def deg2rad(angle):
		""" Convert angle in degrees to radians """
		return np.radians(angle)

	@staticmethod
	def gon2rad(angle):
		""" Convert angle in gons to radians """
		return angle * np.pi / 200.0

	@staticmethod
	def mil2rad(angle):
		""" Convert angle in mils to radians """
		return angle * np.pi / 3200.0

	@staticmethod
	def dm2rad(dm):
		""" Convert angle given as (d,m) tuple to radians """
		d, m = dm
		s = 0
		return Angle.dms2rad((d, m, s))

	@staticmethod
	def dms2rad(dms):
		""" Convert angle given as (d,m,s) tuple to radians """
		d, m, s = dms
		sign = np.sign(d)
		d = np.abs(d)
		return sign * (d + m / 60. + s / 3600.) * np.pi / 180.0

	## These methods change the angle value in place

	def constrain360(self):
		""" Constrain angle to domain (0, 2*np.pi) """
		self.__val = np.remainder(self.__val, 2.0 * np.pi)

	def constrain180(self):
		""" Constrain angle to domain (-np.pi, +np.pi) """
		self.constrain360()
		if np.isscalar(self.__val):
			if self.__val > np.pi:
				self.__val -= (2.0 * np.pi)
		else:
			self.__val[self.__val > np.pi] -= (2.0 * np.pi)

	## The following methods return new objects
	## Note the use of self.__class__() instead of Angle(),
	## so that derived classes return objects of the same class

	def to_azimuth(self):
		""" Convert mathematical angle to azimuth constrained to (0, 2*np.pi) """
		return Azimuth(self.get_complement().__float__())

	def to_angle(self):
		return self

	def to_other_angle_type(self):
		"""
		Convert Angle to Azimuth and vice versa
		"""
		if self.is_angle():
			return self.to_azimuth()
		elif self.is_azimuth():
			return self.to_angle()

	def get_complement(self):
		""" Return complementary angle """
		return self.__class__(np.pi / 2.0 - self.__val)

	def get_supplement(self):
		""" Return supplementary angle """
		return self.__class__(np.pi - self.__val)

	def get_reverse(self):
		""" Return reverse angle """
		return self.__class__(self.__val + np.pi)

	## The following methods provide conversions of internally stored angle value
	## in radians to other angle formats

	def rad(self):
		""" Return angle in radians """
		return self.__val

	def deg(self):
		""" Return angle in degrees """
		return np.degrees(self.__val)

	def deground(self):
		return np.int64(np.round(self.deg()))

	def gon(self):
		""" Return angle in gons """
		return self.__val * 200.0 / np.pi

	def mil(self):
		""" Return angle in mils """
		return self.__val * 3200.0 / np.pi

	def dms(self):
		""" Return angle in (d,m,s) tuple """
		d, ms = self.dm()
		m = np.floor(ms)
		s = ms - m
		s *= 60.
		return (d, m, s)

	def dm(self):
		""" Return angle in (d,m) tuple """
		angle = self.deg()
		d = np.floor(angle)
		ms = np.abs(angle * 100. - d * 100.)
		ms *= (60. / 100.)
		return (d, ms)

	## The following methods are necessary for compatibility with numpy functions

	def cos(self):
		return np.cos(self.__val)

	def sin(self):
		return np.sin(self.__val)

	def tan(self):
		return np.tan(self.__val)

	def sqrt(self):
		return np.sqrt(self.__val)

	def log(self):
		return np.log(self.__val)

	def log10(self):
		return np.log10(self.__val)

	def pow(self, y):
		return np.power(self.__val, y)

	degrees = deg
	radians = rad

	def mean(self, weights=None):
		"""
		Compute mean angle/azimuth

		:param weights:
			float array, weights corresponding to different angles
			if instance is not scalar

		:return:
			instance of :class:`Angle` or :class:`Azimuth`
		"""
		## Mean Y component
		sa = np.average(np.sin(self.__val), weights=weights)
		## Mean X component
		ca = np.average(np.cos(self.__val), weights=weights)
		## Take the arctan of the averages
		return self.__class__(np.arctan2(sa, ca))

	def degmean(self, weights=None):
		"""
		Compute mean angle/azimuth in degrees.

		:param weights:
			See :meth:`mean`
		"""
		mean_angle = self.mean(weights=weights)
		return mean_angle.deg()

	def to_unit_vector(self):
		"""
		Convert angle to unit vector

		:return:
			tuple of X and Y components of unit vector
		"""
		vx = np.cos(self.__val)
		vy = np.sin(self.__val)
		return (vx, vy)

	def get_enclosed_angle(self, other_angle):
		"""
		Compute enclosed angle between this angle and another one
		"""
		assert (isinstance(other_angle, Angle)
				and not other_angle.is_other_angle_type(other_angle))
		"""
		v1x, v1y = self.to_unit_vector()
		v2x, v2y = other_angle.to_unit_vector()

		delta_rad = np.arctan2(v2y, v2x) - np.arctan2(v1y, v1x)
		## This should be equivalent, but does not support non-scalar angles
		#delta_rad = np.arccos(np.dot(v1, v2))

		if np.isscalar(delta_rad):
			if np.isnan(delta_rad):
				if (v1 == v2).all():
					delta_rad = 0.0
				else:
					delta_rad = np.pi
		else:
			is_nan = np.isnan(delta_rad)
			delta_rad[is_nan] = np.pi
			idxs = is_nan & (v1x == v2x) & (v1y == v2y)
			delta_rad[idxs] = 0.

		return self.__class__(np.abs(delta_rad))
		"""
		delta1 = self - other_angle
		delta2 = other_angle - self

		return self.__class__(np.min([np.abs(delta1), np.abs(delta2)], axis=0))


class Azimuth(Angle):
	"""
	Class Azimuth implements a special object for geographic azimuths.
	Azimuths are measured clockwise from grid north.

	This class is derived from class Angle. The value is again internally stored as
	radians, but is now constrained to domain (0, 2*np.pi).

	An additional method to_angle() converts the azimuth back to the corresponding
	mathematical angle, returning an Angle object.
	"""
	def __init__(self, val, format="rad"):
		Angle.__init__(self, val, format)

		# Override constrain to constrain360
		self.constrain360()

	## It is not necessary to override magic methods defined in Angle

	## The following methods are needed to distinguish and convert
	## between Angle and Azimuth

	def is_angle(self):
		return False

	def is_azimuth(self):
		return True

	def to_azimuth(self):
		return self

	def to_angle(self):
		""" Convert azimuth to mathematical angle """
		return Angle(self.get_complement().__float__())

	def toDirectionEast(self):
		if self.__float__() > np.pi:
			return self.get_complement()
		else:
			return self

	def get_cardinal_direction(self):
		"""
		A cardinal direction is one of sixteen directions such as
		North, South, SouthEast, WestSouthWest, and so on.
		This function is most useful for providing an "in English"
		representation of an azimuth.
		"""
		degval = self.deg()
		if 11.25 < degval < 33.75:
			dir = "NNE"
		elif 33.75 <= degval <= 56.25:
			dir = "NE"
		elif 56.25 < degval < 78.75:
			dir = "ENE"
		elif 78.75 <= degval <= 101.25:
			dir = "E"
		elif 101.25 < degval < 123.75:
			dir = "ESE"
		elif 123.75 <= degval <= 146.25:
			dir = "SE"
		elif 146.25 < degval < 168.75:
			dir = "SSE"
		elif 168.75 <= degval <= 191.25:
			dir = "S"
		elif 191.25 < degval < 213.75:
			dir = "SSW"
		elif 213.75 <= degval <= 236.25:
			dir = "SW"
		elif 236.25 < degval < 258.75:
			dir = "WSW"
		elif 258.75 <= degval <= 291.25:
			dir = "W"
		elif 291.25 < degval < 303.75:
			dir = "WNW"
		elif 303.75 <= degval <= 326.25:
			dir = "NW"
		elif 326.25 < degval < 348.75:
			dir = "NNW"
		else:
			dir = "N"
		return dir


def asin(val):
	return Angle(np.arcsin(val))

def acos(val):
		return Angle(np.arccos(val))

def atan(val):
		return Angle(np.arctan(val))

def atan2(y, x):
	return Angle(np.arctan2(y, x))



if __name__ == '__main__':
	a = Angle(180, "deg")
	print(a.rad())
	print(a.deg())
	print(a.gon())
	print(a.mil())
	print(a.dms())
	print(a.dm())
	b = Angle(np.pi)
	c = a * b
	print(b.to_azimuth().get_cardinal_direction())
	print(atan2(50, 10).deg())
