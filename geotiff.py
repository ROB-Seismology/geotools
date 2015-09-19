"""
Write single-band and multi-band GeoTiffs
"""

import numpy as np
import PIL
import gdal, osr


def write_single_band_geotiff(out_filespec, data, extent, srs, cell_registration="center",
								north_up=False, nodata_value=np.nan):
	"""
	Write data array to single-band GeoTiff

	:param out_filespec:
		str, full path to output TIF file
	:param data:
		2-D [y,x] numpy array with data values
	:param extent:
		(xmin, xmax, ymin, ymax) tuple of floats: grid extent
	:param srs:
		instance of class:`osr.SpatialReferenceSystem` or str: spatial
		reference system or WKT representation
	:param cell_registration:
		str, one of "center" or "corner": whether coordinates in :param:`extent`
		correspond to cell center or cell corner
		(default: "center")
	:param north_up:
		bool, whether or not 2nd dimension of :param:`data` is north-up
		(i.e., going from xmax to xmin)
		(default: False)
	:param nodata_value:
		float, value to use for "no data"
		(default: np.nan)
	"""
	## Order of rows should be north to south, otherwise image is upside down
	if not north_up:
		data = data[::-1,:]
	ny, nx = data.shape

	## GDAL needs grid corner coordinates
	xmin, xmax, ymin, ymax = extent
	if cell_registration == "center":
		dx = (xmax - xmin) / (float(nx) - 1)
		xmin -= dx/2.
		dy = (ymax - ymin) / (float(ny) - 1)
		ymax += dy/2.
	elif cell_registration == "corner":
		dx = (xmax - xmin) / float(nx)
		dy = (ymax - ymin) / float(ny)

	driver = gdal.GetDriverByName("Gtiff")
	ds = driver.Create(out_filespec, nx, ny, 1, gdal.GDT_Float32)

	## Affine transform takes 6 parameters:
	## top left x, cell size x, rotation, top left y, rotation, cell size y
	## Note that x, y coordinates refer to top left corner of top left pixel!
	## For north-up images, rotation coefficients are zero
	tf = (xmin, dx, 0, ymax, 0, -dy)
	ds.SetGeoTransform(tf)
	try:
		srs_wkt = srs.ExportToWkt()
	except:
		srs_wkt = srs
	ds.SetProjection(srs_wkt)

	band = ds.GetRasterBand(1)
	band.WriteArray(data.astype(np.float32))
	band.SetNoDataValue(nodata_value)
	band.ComputeStatistics()
	ds.FlushCache()


def write_multi_band_geotiff(out_filespec, img, extent, srs, cell_registration="corner",
								north_up=True):
	"""
	Write image data to multi-band GeoTiff

	:param out_filespec:
		str, full path to output TIF file
	:param img:
		instance of class:`PIL.Image` or 3-D numpy array with (y, x, RGB[A])
		values
	:param extent:
		(xmin, xmax, ymin, ymax) tuple of floats: grid extent
	:param srs:
		instance of class:`osr.SpatialReferenceSystem` or str: spatial
		reference system or WKT representation
	:param cell_registration:
		str, one of "center" or "corner": whether coordinates in :param:`extent`
		correspond to cell center or cell corner
		(default: "corner")
	:param north_up:
		bool, whether or not 2nd dimension of :param:`data` is north-up
		(i.e., going from xmax to xmin)
		(default: True)
	"""
	if isinstance(img, PIL.Image.Image):
		img_ar = np.array(img)
	else:
		img_ar = img
	ny, nx, num_bands = img_ar.shape
	print nx, ny, num_bands

	## Order of rows should be north to south, otherwise image is upside down
	if not north_up:
		img_ar = img_ar[::-1,:,:]

	## GDAL needs grid corner coordinates
	xmin, xmax, ymin, ymax = extent
	if cell_registration == "center":
		dx = (xmax - xmin) / (float(nx) - 1)
		xmin -= dx/2.
		dy = (ymax - ymin) / (float(ny) - 1)
		ymax += dy/2.
	elif cell_registration == "corner":
		dx = (xmax - xmin) / float(nx)
		dy = (ymax - ymin) / float(ny)

	driver = gdal.GetDriverByName("Gtiff")
	ds = driver.Create(out_filespec, nx, ny, num_bands, gdal.GDT_Byte)

	## Affine transform takes 6 parameters:
	## top left x, cell size x, rotation, top left y, rotation, cell size y
	## Note that x, y coordinates refer to top left corner of top left pixel!
	## For north-up images, rotation coefficients are zero
	tf = (xmin, dx, 0, ymax, 0, -dy)
	ds.SetGeoTransform(tf)
	try:
		srs_wkt = srs.ExportToWkt()
	except:
		srs_wkt = srs
	ds.SetProjection(srs_wkt)

	for i in range(num_bands):
		band = ds.GetRasterBand(i+1)
		band.WriteArray(img_ar[:,:,i])
	ds.FlushCache()

