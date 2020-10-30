# -*- coding: iso-Latin-1 -*-

"""
Create buffer around geometry
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import numpy as np
from . import coordtrans as ct
from .read_gis import read_gis_file
import mapping.layeredbasemap as lbm



def create_buffer_polygon(gis_file, buffer_distance, show_plot=False):
	"""
	Create buffer polygon for a country or region.

	:param gis_file:
		str, full path to GIS file containing country border
		Note: the main polygon from the first record will be selected
	:param buffer_distance:
		float, buffer distance (in km)
	:param show_plot:
		bool, whether or not a plot of the country border and buffer
		should be shown
		(default: False)

	:return:
		OGR Geometry object
	"""
	## Read main polygon
	#gis_data = lbm.GisData(gis_file)
	#_, _, polygon_data = gis_data.get_data()
	recs = read_gis_file(gis_file, verbose=False)
	geom = recs[0]['obj']
	geom.CloseRings()
	polygon_data = lbm.MultiPolygonData.from_ogr(geom)

	## Select main polygon
	main_pg, pg_len = None, 0
	for p, pg in enumerate(polygon_data):
		if len(pg.lons) > pg_len:
			main_pg = pg
			pg_len = len(pg.lons)

	## Determine UTM projection
	centroid = main_pg.get_centroid()
	utm_spec = ct.get_utm_spec(centroid.lon, centroid.lat)
	utm_srs = ct.get_utm_srs(utm_spec)

	## Reproject main polygon to UTM
	lons, lats = ct.transform_array_coordinates(ct.WGS84, utm_srs,
															main_pg.lons, main_pg.lats)
	main_pg.lons, main_pg.lats = list(lons), list(lats)
	main_pg.interior_lons = main_pg.interior_lats = main_pg.interior_z = []
	#print(main_pg.to_wkt())

	## Create buffer polygon
	if buffer_distance:
		buffer_pg = main_pg.create_buffer(buffer_distance * 1000)
	else:
		buffer_pg = main_pg

	if show_plot:
		import pylab

		pylab.plot(main_pg.lons, main_pg.lats)
		pylab.plot(buffer_pg.lons, buffer_pg.lats)
		pylab.show()

	## Reproject buffer polygon to lon, lat
	lons, lats = ct.transform_array_coordinates(utm_srs, ct.WGS84,
														buffer_pg.lons, buffer_pg.lats)
	buffer_pg.lons = lons
	buffer_pg.lats = lats

	if show_plot:
		pylab.plot(buffer_pg.lons, buffer_pg.lats)
		pylab.show()

	return buffer_pg.to_ogr_geom()
