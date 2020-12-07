"""
Fix imprecise implementation of Lambert1972 coordinate system
in older MapInfo files
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import os
import osr, ogr, gdal

gdal.UseExceptions()


def backup_mi_file(mi_filespec, backup_filespec="", overwrite=False):
	extensions = [".TAB", ".DAT", ".MAP", ".ID", ".IND"]
	folder, filename = os.path.split(mi_filespec)
	basename, _ = os.path.splitext(filename)
	if backup_filespec:
		backup_folder, backup_filename = os.path.split(backup_filespec)
		backup_basename, _ = os.path.splitext(backup_filename)
	else:
		backup_folder = folder
		backup_basename = "Copy of " + basename
	for ext in extensions:
		filespec = os.path.join(folder, basename + ext)
		backup_filespec = os.path.join(backup_folder, backup_basename + ext)
		if os.path.exists(filespec):
			if os.path.exists(backup_filespec):
				if overwrite:
					os.unlink(backup_filespec)
				else:
					print("Warning: not overwriting backup file %s!"
							% backup_filespec)
					return
			os.rename(filespec, backup_filespec)


def fix_mi_lambert_ogr(mi_filespec, overwrite_backup=False):
	from mapping.geotools.coordtrans import LAMBERT1972

	in_ds = ogr.Open(mi_filespec, 0)

	## Non-vector MapInfo files cannot be read by ogr, try with MIPython
	if in_ds is None and os.path.exists(mi_filespec):
		return fix_mi_lambert(mi_filespec, overwrite_backup=overwrite_backup)

	in_layer = in_ds.GetLayer(0)
	in_srs = in_layer.GetSpatialRef()
	wkt = in_srs.ExportToWkt()
	if ('DATUM["Belgium_Hayford' in wkt or 'DATUM["MIF 999' in wkt
		or 'TOWGS84[0,0,0,0,0,0,0]' in wkt):
		if in_srs.IsProjected():
			print("Fixing %s... with ogr/gdal" % mi_filespec)
			#in_srs.CopyGeogCSFrom(lambert1972)

			folder, filename = os.path.split(mi_filespec)
			basename, ext = os.path.splitext(filename)

			## Create backup first
			backup_filespec = os.path.join(folder, basename + " (old lambert72)" + ext)
			print("Copying backup file %s" % backup_filespec)
			in_ds.Destroy()
			backup_mi_file(mi_filespec, backup_filespec, overwrite=overwrite_backup)
			in_ds = ogr.Open(backup_filespec, 0)
			in_layer = in_ds.GetLayer(0)

			## Create the output tab file
			driver = ogr.GetDriverByName("MapInfo File")
			out_ds = driver.CreateDataSource(mi_filespec)

			## Create the output Layer
			## If input geometry type is wkbUnknown, output features are not
			## created, so we just set linestring, but it doesn't really matter
			geom_type = in_layer.GetGeomType() or ogr.wkbLineString
			out_layer = out_ds.CreateLayer(in_layer.GetName(), srs=LAMBERT1972,
												geom_type=geom_type)

			## Copy input Layer Fields to the output Layer
			in_layer_defn = in_layer.GetLayerDefn()
			for i in range(in_layer_defn.GetFieldCount()):
				field_defn = in_layer_defn.GetFieldDefn(i)
				out_layer.CreateField(field_defn)

			## Get the output Layer's Feature Definition
			out_layer_defn = out_layer.GetLayerDefn()

			## Add features to the ouput Layer
			for in_feature in in_layer:
				## Create output Feature
				out_feature = ogr.Feature(out_layer_defn)

				## Add field values from input Layer
				for i in range(out_layer_defn.GetFieldCount()):
					field_defn = out_layer_defn.GetFieldDefn(i)
					out_feature.SetField(out_layer_defn.GetFieldDefn(i).GetNameRef(),
												in_feature.GetField(i))

				## Set geometry if present
				geom = in_feature.GetGeometryRef()
				if geom:
					#wkt = geom.ExportToWkt()
					out_feature.SetGeometry(geom.Clone())
					#out_geom = ogr.CreateGeometryFromWkt(wkt)
					#out_feature.SetGeometry(out_geom)

				## Add new feature to output Layer
				errcode = out_layer.CreateFeature(out_feature)
				#print(errcode)

				## Destroy the feature to free resources
				out_feature.Destroy()

			out_layer.SyncToDisk()

			# Close DataSources
			in_ds.Destroy()
			out_ds.Destroy()

		else:
			## Longitude / Latitude (Belgium): does not seem to be problematic
			print("Warning: %s has older MapInfo implementation of Lambert1972, not fixed!"
					% mi_filespec)



def fix_mi_lambert(mi_filespec, overwrite_backup=False):
	import mapping.MIPython as MI

	app = MI.Application()
	tab = app.OpenTable(mi_filespec)
	coordsys = tab.GetCoordsys()
	bounds = coordsys.GetBounds()
	coordsys.DropBounds()

	old_lambert_clauses = ['CoordSys Earth Projection 1, 110',
		'CoordSys Earth Projection 19, 110, "m", 4.3569397222, 90.0, 49.8333333333, 51.1666666667, 150000.01256, 5400088.4378']
	new_lambert_clauses = ['CoordSys Earth Projection 1, 1019',
		'CoordSys Earth Projection 3, 1019, "m", 4.3674866667, 90.0, 49.8333339, 51.1666672333, 150000.013, 5400088.438']

	try:
		idx = old_lambert_clauses.index(coordsys.Clause())
	except:
		tab.Close()
	else:
		new_lambert_clause = new_lambert_clauses[idx]
		print("Fixing %s... with MIPython" % mi_filespec)

		## Create backup first
		tab.Close()
		folder, filename = os.path.split(mi_filespec)
		basename, ext = os.path.splitext(filename)
		backup_filespec = os.path.join(folder, basename + " (old lambert72)" + ext)
		print("Copying backup file %s" % backup_filespec)
		backup_mi_file(mi_filespec, backup_filespec, overwrite=overwrite_backup)
		tab = app.OpenTable(backup_filespec)
		tab.Backup(mi_filespec)
		tab.Close()

		## Fix coordinate system
		tab = app.OpenTable(mi_filespec)
		coordsys.FromClause(new_lambert_clause)
		if bounds:
			coordsys.SetBounds(bounds)
		tab.SetCoordsys(coordsys, backup=False)
		tab.Close()


def fix_mi_lambert_folder_ogr(folder, overwrite_backup=False):
	for dirpath, dirnames, filenames in os.walk(folder):
		for filename in filenames:
			if (os.path.splitext(filename)[-1].upper() == ".TAB"
				and not "old lambert72" in filename):
				mi_filespec = os.path.join(dirpath, filename)
				fix_mi_lambert_ogr(mi_filespec, overwrite_backup=overwrite_backup)



if __name__ == "__main__":
	mi_filespec = "C:\\Temp\\MI\\QUAT_18_BREUK.tab"
	#mi_filespec = "C:\\Temp\\MI\\Quaternary\\BasisQ_18.TAB"
	#backup_mi_file(mi_filespec, "C:\\Temp\\MI\\QUAT_18_BREUK (old lambert72).tab", overwrite=True)

	#fix_mi_lambert_ogr(mi_filespec)
	folder = "D:\\GIS-data\\Paleosis\\Digitized\\17-8-Peer"
	fix_mi_lambert_folder_ogr(folder)
