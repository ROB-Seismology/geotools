
import os


def fix_mi_lambert_ogr(gis_filespec):
	import ogr, osr
	from mapping.geo.coordtrans import lambert1972

	ds = ogr.Open(gis_filespec, 0)
	layer = ds.GetLayer(0)
	tab_srs = layer.GetSpatialRef()
	if 'DATUM["Belgium_Hayford"' in tab_srs.ExportToWkt():
		if tab_srs.IsProjected():
			tab_srs.CopyGeogCSFrom(lambert1972)
			layer.SyncToDisk()
		else:
			# TODO
			print("Warning: older MapInfo implementation of Lambert1972, coordinates may be shifted!")


def fix_mi_lambert(gis_filespec):
	import mapping.MIPython as MI

	app = MI.Application()
	tab = app.OpenTable(gis_filespec)
	coordsys = tab.GetCoordsys()
	bounds = coordsys.GetBounds()
	coordsys.DropBounds()

	old_lambert_clause = 'CoordSys Earth Projection 19, 110, "m", 4.3569397222, 90.0, 49.8333333333, 51.1666666667, 150000.01256, 5400088.4378'
	new_lambert_clause = 'CoordSys Earth Projection 3, 1019, "m", 4.3674866667, 90.0, 49.8333339, 51.1666672333, 150000.013, 5400088.438'

	if coordsys.Clause() == old_lambert_clause:
		print("Fixing older MapInfo implementation of Lambert1972...")
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
			if os.path.exists(backup_filespec):
				print("Removing backup copy...")
				os.unlink(backup_filespec)
			tab.Close()

	else:
		print coordsys.Clause()


if __name__ == "__main__":
	gis_filespec = r"C:\Temp\MI\QUAT_26_TERRASGRENS.tab"
	fix_mi_lambert(gis_filespec)
