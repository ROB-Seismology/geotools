
import os
import osr, ogr, gdal

gdal.UseExceptions()


def fix_mi_lambert_ogr(gis_filespec):
	from mapping.geo.coordtrans import lambert1972

	in_ds = ogr.Open(gis_filespec, 0)
	in_layer = in_ds.GetLayer(0)
	in_srs = in_layer.GetSpatialRef()
	if 'DATUM["Belgium_Hayford"' in in_srs.ExportToWkt():
		if in_srs.IsProjected():
			print("Fixing %s..." % gis_filespec)
			#in_srs.CopyGeogCSFrom(lambert1972)
			#layer.SyncToDisk()

			# Create the output Layer
			folder, filename = os.path.split(gis_filespec)
			basename, ext = os.path.splitext(filename)
			backup_filespec = os.path.join(folder, basename + " (old lambert72)" + ext)
			out_filespec = os.path.join(folder, "Copy of " + filename)
			driver = ogr.GetDriverByName("MapInfo File")

			# Remove output tab file if it already exists
			if os.path.exists(out_filespec):
				driver.DeleteDataSource(out_filespec)

			# Create the output tab file
			out_ds = driver.CreateDataSource(out_filespec)
			out_lyr_name = os.path.splitext(filename)[0]
			out_layer = out_ds.CreateLayer(out_lyr_name, srs=lambert1972, geom_type=in_layer.GetGeomType())

			# Copy input Layer Fields to the output Layer
			in_layer_defn = in_layer.GetLayerDefn()
			for i in range(0, in_layer_defn.GetFieldCount()):
				field_defn = in_layer_defn.GetFieldDefn(i)
				out_layer.CreateField(field_defn)

			# Get the output Layer's Feature Definition
			out_layer_defn = out_layer.GetLayerDefn()

			# Add features to the ouput Layer
			for in_feature in in_layer:
				# Create output Feature
				out_feature = ogr.Feature(out_layer_defn)

				# Add field values from input Layer
				for i in range(0, out_layer_defn.GetFieldCount()):
					field_defn = out_layer_defn.GetFieldDefn(i)
					out_feature.SetField(out_layer_defn.GetFieldDefn(i).GetNameRef(),
						in_feature.GetField(i))

				# Set geometry
				geom = in_feature.GetGeometryRef()
				out_feature.SetGeometry(geom.Clone())

				# Add new feature to output Layer
				out_layer.CreateFeature(out_feature)

				# Destroy the feature to free resources
				out_feature.Destroy()

			# Close DataSources
			driver.CopyDataSource(in_ds, backup_filespec)
			in_ds.Destroy()
			driver.DeleteDataSource(gis_filespec)
			driver.CopyDataSource(out_ds, gis_filespec)
			out_ds.Destroy()
			driver.DeleteDataSource(out_filespec)

		else:
			# TODO
			print("Warning: older MapInfo implementation of Lambert1972, coordinates may be shifted!")



def fix_mi_lambert(gis_filespec, remove_backup=False):
	import mapping.MIPython as MI

	app = MI.Application()
	tab = app.OpenTable(gis_filespec)
	coordsys = tab.GetCoordsys()
	bounds = coordsys.GetBounds()
	coordsys.DropBounds()

	old_lambert_clause = 'CoordSys Earth Projection 19, 110, "m", 4.3569397222, 90.0, 49.8333333333, 51.1666666667, 150000.01256, 5400088.4378'
	new_lambert_clause = 'CoordSys Earth Projection 3, 1019, "m", 4.3674866667, 90.0, 49.8333339, 51.1666672333, 150000.013, 5400088.438'

	if coordsys.Clause() == old_lambert_clause:
		print("Fixing %s..." % gis_filespec)
		coordsys.FromClause(new_lambert_clause)
		coordsys.SetBounds(bounds)
		tab.SetCoordsys(coordsys)
		tab.Close()

		try:
			tab = app.OpenTable(gis_filespec)
		except:
			raise
		else:
			folder, filename = os.path.split(gis_filespec)
			backup_filespec = os.path.join(folder, "Copy of " + filename)
			if remove_backup and os.path.exists(backup_filespec):
				print("Removing backup copy...")
				backup_tab = app.OpenTable(backup_filespec)
				backup_tab.Drop()
			tab.Close()

	else:
		print coordsys.Clause()


def fix_mi_lambert_folder(folder, remove_backup=False):
	for dirpath, dirnames, filenames in os.walk(folder):
		for filename in filenames:
			if os.path.splitext(filename)[-1].upper() == ".TAB":
				mi_filespec = os.path.join(dirpath, filename)
				fix_mi_lambert(mi_filespec, remove_backup=remove_backup)


if __name__ == "__main__":
	#gis_filespec = r"C:\Temp\MI\QUAT_18_TERRASGRENS.tab"
	#gis_filespec = r"C:\Temp\MI\Quaternary\BasisQ_18.TAB"
	#fix_mi_lambert(gis_filespec)
	folder = r"C:\Temp\MI\Quaternary"
	fix_mi_lambert_folder(folder)

