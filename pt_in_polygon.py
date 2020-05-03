"""
Select points in polygon
"""

from __future__ import absolute_import, division, print_function, unicode_literals


from osgeo import ogr


__all__ = ['filter_points_by_polygon']


def filter_points_by_polygon(longitudes, latitudes, poly_obj):
	"""
	Subselect points from a point collection that are situated
	inside a polygon

	:param longitudes:
		array-like, longitudes (in degrees)
	:param latitudes:
		array-like, latitudes (in degrees)
	:param poly_obj:
		polygon or closed linestring object (ogr geometry object
		or oqhazlib.geo.polygon.Polygon object)

	:return:
		(points_inside, points_outside) tuple
		lists with indexes of points that are inside/outside the polygon
	"""
	points_inside, points_outside = [], []

	## First try converting poly_obj to ogr geometry if this is supported
	if hasattr(poly_obj, 'to_ogr_geom'):
		poly_obj = poly_obj.to_ogr_geom()
	elif hasattr(poly_obj, 'to_ogr_geometry'):
		poly_obj = poly_obj.to_ogr_geometry()

	if isinstance(poly_obj, ogr.Geometry):
		## Construct WGS84 projection system corresponding to earthquake coordinates
		from .coordtrans import WGS84

		## Point object that will be used to test if earthquake is inside zone
		point = ogr.Geometry(ogr.wkbPoint)
		point.AssignSpatialReference(WGS84)

		if poly_obj.GetGeometryName() in ("MULTIPOLYGON", "POLYGON", "LINESTRING"):
			## Objects other than polygons or closed polylines will be skipped
			if poly_obj.GetGeometryName() == "LINESTRING":
				line_obj = poly_obj
				if line_obj.IsRing() and line_obj.GetPointCount() > 3:
					## Note: Could not find a way to convert linestrings to polygons
					## The following only works for linearrings (what is the difference??)
					#poly_obj = ogr.Geometry(ogr.wkbPolygon)
					#poly_obj.AddGeometry(line_obj)
					wkt = line_obj.ExportToWkt().replace("LINESTRING (", "POLYGON ((") + ")"
					poly_obj = ogr.CreateGeometryFromWkt(wkt)
				else:
					return None
			for idx, (lon, lat) in enumerate(zip(longitudes, latitudes)):
				point.SetPoint(0, lon, lat)
				if point.Within(poly_obj):
					points_inside.append(idx)
				else:
					points_outside.append(idx)

		else:
			msg = 'Warning: %s not a polygon geometry!'
			msg %= poly_obj.GetGeometryName()
			print(msg)

	else:
		import openquake.hazardlib as oqhazlib
		if isinstance(poly_obj, oqhazlib.geo.Polygon):
			mesh = oqhazlib.geo.Mesh(longitudes, latitudes, depths=None)
			intersects = poly_obj.intersects(mesh)
			in_polygon = (intersects == True)
			for idx in range(len(in_polygon)):
				if in_polygon[idx]:
					points_inside.append(idx)
				else:
					points_outside.append(idx)
		else:
			raise Exception("poly_obj not recognized!")

	return points_inside, points_outside
