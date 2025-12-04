#! /usr/bin/env python3

import struct, os, argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# pip install numpy
import numpy as np

# pip install scipy
from scipy.ndimage import rotate

# pip install pynrrd
import nrrd

Header = dict[str, object]

def et_get_val (root: ET.Element, path: str) -> str:
	e = root.find(path)
	assert e is not None
	v = e.get("value")
	assert v is not None
	return v

def pretty_xml (xml: str) -> str:
	dom = minidom.parseString(xml)
	return dom.toprettyxml(indent="  ")

class Loader:

	def __init__ (self, path: str) -> None:
		f = open(path, 'rb')
		self.f = f

		n = struct.unpack("<I", f.read(4))[0]
		data = f.read(n)
		assert data.decode('ascii') == "JmVolumeVersion=1"

		# XML
		n = struct.unpack("<I", f.read(4))[0]
		self.xml = f.read(n).decode('shift_jis')
		root = ET.fromstring(self.xml)
		self.Sx = float(et_get_val(root, ".//Attribute/tfXGridSize"))
		self.Sy = float(et_get_val(root, ".//Attribute/tfYGridSize"))
		self.Sz = float(et_get_val(root, ".//Attribute/tfZGridSize"))
		self.rot_angle_deg = float(et_get_val(root, ".//Attribute/tfAntiAliasAngleInDegree"))
		if self.rot_angle_deg == int(self.rot_angle_deg):
			self.rot_angle_deg = int(self.rot_angle_deg)

		n = struct.unpack("<I", f.read(4))[0]
		data = f.read(n)
		assert data.decode('ascii') == "CArray3D"

		# X limits
		x_min, x_max = struct.unpack("<ii", f.read(8))
		self.X = x_max - x_min + 1

		# Y limits
		y_min, y_max = struct.unpack("<ii", f.read(8))
		self.Y = y_max - y_min + 1

		# Z limits
		z_min, z_max = struct.unpack("<ii", f.read(8))
		self.Z = z_max - z_min + 1

		self.byte_skip = f.tell()

	def load_data (self) -> np.ndarray:
		"""Load voxels."""

		self.f.seek(self.byte_skip)
		data = np.frombuffer(self.f.read(), dtype=np.int16)
		assert len(data) == self.X * self.Y * self.Z
		return data.reshape((self.X, self.Y, self.Z))

	def __enter__(self) -> "Loader":
		return self

	def __exit__ (self, *exc) -> None:
		if not self.f.closed:
			self.f.close()

	def __del__ (self) -> None:
		if not self.f.closed:
			self.f.close()

def header_to_nhdr (header: Header) -> str:
	return f"""NRRD0004
# Complete NRRD file format specification at:
# http://teem.sourceforge.net/nrrd/format.html
type: {header['type']}
dimension: {header['dimension']}
space: {header['space']}
sizes: {' '.join(map(str, header['sizes']))}
space directions: {' '.join(map(lambda x: str(x).replace(' ', ''), header['space directions']))}
kinds: {' '.join(header['kinds'])}
endian: {header['endian']}
encoding: {header['encoding']}
space origin: {str(header['space origin']).replace(' ', '')}
byte skip: {header['byte skip']}
data file: {header['data file']}
"""

def main () -> None:
	ap = argparse.ArgumentParser(description="Convert Morita .vol to .nrrd")
	ap.add_argument("--output-extension", choices=("auto", "nrrd", "nhdr"), default="auto")
	ap.add_argument("--extract-header", action="store_true")
	ap.add_argument("path")
	args = ap.parse_args()

	with Loader(args.path) as loader:
		ext = args.output_extension
		if ext == "auto":
			if loader.rot_angle_deg != 0:
				ext = "nrrd"
			else:
				ext = "nhdr"

		header: Header = {
			'type': 'signed short',
			'space': 'left-posterior-superior',
			'kinds': ('domain', 'domain', 'domain'),
			'space origin': (0, 0, 0),
			'space directions': (
				(0, 0, loader.Sz),
				(loader.Sx, 0, 0),
				(0, loader.Sy, 0),
			)
		}

		if ext == "nrrd":
			data = loader.load_data()
			if loader.rot_angle_deg != 0:
				print(f"rotating by {loader.rot_angle_deg}°...")
				# rotate around last axis (2), relative to center
				data = rotate(data, angle=loader.rot_angle_deg, axes=(0, 1), reshape=False, order=1, cval=-32768)
				# flip very first (0) axis
				data = data[::-1, :, :]
				assert loader.Sx == loader.Sy
				header['space directions'] = (
					(0, 0, loader.Sz),
					(0, loader.Sy, 0),
					(loader.Sx, 0, 0),
				)
			header['encoding'] = 'gzip'
			nrrd.write(
				file = os.path.splitext(args.path)[0] + "." + ext,
				data = data,
				header = header,
				detached_header = False,
				index_order = 'C'
			)
		elif ext == "nhdr":
			header['encoding'] = 'raw'
			header['endian'] = 'little'
			header['byte skip'] = loader.byte_skip
			header['data file'] = os.path.basename(args.path)
			header["dimension"] = 3
			header["sizes"] = (loader.Z, loader.Y, loader.X)
			with open(os.path.splitext(args.path)[0] + "." + ext, "w") as f:
				f.write(header_to_nhdr(header))
		else:
			raise RuntimeError()

		if args.extract_header:
			with open(args.path + ".header.xml", "w", encoding="utf-8") as f:
				f.write(pretty_xml(loader.xml))

if __name__ == '__main__':
	main()
