"""
Some functions related to DGPS processing with rtklib
"""

import os
import subprocess
import numpy as np

from mapping.geo.coordtrans import lonlat_to_lambert1972


RTKLIB_FOLDER = r"C:\Geo\rtklib"


def rtkpost(rover_obs_file, ref_obs_file, ref_nav_files, conf_file, split_file=""):
	"""
	Post-process GPS position using command-line version of rtkpost

	:param rover_obs_file:
		str, full path to Rinex OBS file containing rover observations
	:param ref_obs_file:
		str, full path to Rinex OBS file containing base station observations
	:param ref_nav_files:
		list of str, full paths to Rinex NAV/GNAV/HNAV files for base station
	:param conf_file:
		str, full path to rtkpost configuration file
	:param split_file,
		str, full path to CSV file containing start and end dates and times
		for separate points in rover observation file
		(default: "")
	"""
	rnx2rtkp = os.path.join(RTKLIB_FOLDER, "bin", "rnx2rtkp.exe")
	folder = os.path.split(rover_obs_file)[0]
	rover_obs_file = os.path.relpath(rover_obs_file, folder)
	ref_obs_file = os.path.relpath(ref_obs_file, folder)
	ref_nav_files = [os.path.relpath(file, folder) for file in ref_nav_files]
	conf_file = os.path.relpath(conf_file, folder)
	cmd_list = []
	if not split_file:
		pos_file = os.path.splitext(rover_obs_file)[0] + '.pos'
		cmd = '%s -k "%s" -o "%s" "%s" %s'
		cmd %= (rnx2rtkp, conf_file, pos_file, rover_obs_file, ref_obs_file, "".join(['"%s"' % f for f in ref_nav_files]))
		cmd_list.append(cmd)
	else:
		base_cmd = '%s -k "%s" -o POS_FILE TIME_STUB "%s" "%s" %s'
		base_cmd %= (rnx2rtkp, conf_file, rover_obs_file, ref_obs_file, "".join(['"%s"' % f for f in ref_nav_files]))

		with open(split_file) as fd:
			for line in fd:
				if line[0] != '#':
					pt_name, start_dt, end_dt = line.split(',')[:3]
					ds, ts = start_dt.split()
					ds = ds.replace('-', '/')
					de, te = end_dt.split()
					de = de.replace('-', '/')

					pos_file = os.path.splitext(rover_obs_file)[0] + '_%s.pos' % pt_name
					cmd = base_cmd.replace('POS_FILE', '"%s"' % pos_file)
					time_stub = "-ts %s %s -te %s %s" % (ds, ts, de, te)
					cmd = cmd.replace("TIME_STUB", time_stub)
					cmd_list.append(cmd)

	for cmd in cmd_list:
		print cmd
		child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=folder)
		input = None
		outdata, errdata = child.communicate(input)
		#for line in errdata:
		#	print line
		child.wait()


def rtklib_pos_to_lambert(pos_filespec, overwrite=False):
	"""
	Convert rtklib solution to Belgian Lambert 1972 coordinates

	:param pos_filespec:
		str, full path to rtklib solution file or to folder containing
		pos files
		If folder is specified, all pos files will be converted separately
		and an additional aggregated file will be created containing all
		converted results.
	:param overwrite:
		bool, whether or not to overwrite lam file
		(default: False)
	"""
	if os.path.isdir(pos_filespec):
		folder = pos_filespec
		pos_filenames = [file for file in os.listdir(folder) if os.path.splitext(file)[-1].lower() == '.pos']
		pos_filespecs = [os.path.join(folder, file) for file in pos_filenames]
		overall_filespec = os.path.join(folder, os.path.split(folder)[-1] + '.lam')
	else:
		pos_filespecs = [pos_filespec]
		overall_filespec = ""

	header = "date, time, easting(m), northing(m), height(m), Q, ns, sdn(m), sde(m), sdu(m), sdne(m), sdeu(m), sdun(m), age(s), ratio"

	if overall_filespec:
		overall_fd = open(overall_filespec, 'w')
		overall_fd.write("name, %s\n" % header)
	else:
		overall_fd = None

	for pos_filespec in pos_filespecs:
		dates, times = [], []
		lons, lats, elevs = [], [], []
		other_infos = []
		with open(pos_filespec) as fd:
			for line in fd:
				if line[0] == '%':
					if len(line) > 2 and line[2] == '(':
						srs, height = line[3:].split(',')[0].split('=')[1].split('/')
						if srs != "WGS84":
							raise Exception("%s reference system not supported" % srs)
				else:
					fields = line.split()
					date, time = fields[:2]
					dates.append(date)
					times.append(time)
					lat, lon, h = map(float, fields[2:5])
					lons.append(lon)
					lats.append(lat)
					elevs.append(h)
					other_infos.append(", ".join(fields[6:]))

			lons = np.array(lons)
			lats = np.array(lats)
			elevs = np.array(elevs)

		if height == "geodetic":
			print("Warning: Geodetic elevations may not correspond to TAW!")
			X, Y = zip(*lonlat_to_lambert1972(zip(lons, lats)))
			Z = elevs
		elif height == "ellipsoidal":
			# Note: this appears incorrect!
			#X, Y, Z = zip(*lonlat_to_lambert1972(zip(lons, lats, elevs)))

			## Z_TAW = Z_ETRS89 - hBG03
			import mapping.Basemap as lbm
			hBG03_filespec = r"D:\seismo-gis\collections\NGI_hBG03\XYZ\hBG03.XYZ"
			hBG03_grd = lbm.GdalRasterData(hBG03_filespec)
			Z = elevs - hBG03_grd.interpolate(lons, lats)

		out_filespec = os.path.splitext(pos_filespec)[0] + '.lam'
		if not os.path.exists(out_filespec) or overwrite:
			with open(out_filespec, 'w') as fd:
				fd.write("%s\n" % header)
				for i in range(len(X)):
					date, time = dates[i], times[i]
					x, y, z = X[i], Y[i], Z[i]
					info = other_infos[i]
					line = "%s, %s, %.3f, %.3f, %.3f, %s\n" % (date, time, x, y, z, info)
					fd.write(line)
					if overall_fd:
						pt_name = os.path.splitext(os.path.split(pos_filespec)[-1])[0]
						line = "%s, %s" % (pt_name, line)
						overall_fd.write(line)
		else:
			print("File %s exists. Use overwrite=True to overwrite" % out_filespec)

	if overall_fd:
		overall_fd.close()



if __name__ == "__main__":
	folder = r"D:\Data\Sites\Grote Brogel\2015-10-29-30 - Galgenstraat Bree\DGPS"

	rover_obs_file = os.path.join(folder, "PROF5.o")
	ref_obs_file = os.path.join(folder, "Flepos", "MAAS3030.15o")
	ref_nav_files = [os.path.join(folder, "Flepos", "MAAS3030.%s" % ext) for ext in ("15n",)]
	split_file = os.path.join(folder, "PROF5.csv")
	conf_file = os.path.join(folder, "rtkpost.conf")
	#rtkpost(rover_obs_file, ref_obs_file, ref_nav_files, conf_file, split_file=split_file)

	#exit()

	folder = r"D:\Data\Sites\Grote Brogel\2015-08-25 - Maarlo\GPS"
	rtklib_pos_to_lambert(folder, overwrite=True)

	exit()

	filenames = os.listdir(folder)
	filenames = [os.path.join(folder, "REF01_ellipsoidal.pos")]
	for filename in filenames:
		if os.path.splitext(filename)[-1].lower() == '.pos':
			pos_filespec = os.path.join(folder, filename)
			print pos_filespec
			rtklib_pos_to_lambert(pos_filespec)
