import geojson
import os

from src import MapSheet
from src.custom_types import Wgs84Coordinate
from src.georeference.baseclasses import ControlPoint, Georeference
from typing import Dict, List
import json

# directory = r'C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\resources'
#
# # iterate over files in
# # that directory
# for root, dirs, files in os.walk(directory):
#     if root == directory+'\bonnebladen':
#         print(root)
# # for filename in files:
# #     print(os.path.join(root, filename))

with open(r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\resources\bonnebladen\10.8.json") as f:
    sheet = MapSheet.from_annotationpage(f.read())

# class CoordinateArray:
#     _coordinates: list["Wgs84Coordinate"]
#     sheetnumber: int
#     def __init__(self, coordinates: list["Wgs84Coordinate"], sheetnumber: int):
#         self._coordinates = coordinates
#         self.sheetnumber = sheetnumber
#
#     def from_geojson_Multipoint(self, gjson) -> "CoordinateArray":
#         #ToDo
#         return self(sheetnumber, coordinates)
#     def a(self):
#        return self._coordinates[0]
#     def b(self):
#        return self._coordinates[1]
#     def c(self):
#        return self._coordinates[2]
#     def d(self):
#        return self._coordinates[3]


with open(r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\phase1\results_wp1\WGS84coordsBBlad.geojson") as f:
    gj = geojson.load(f)
sheetnumber = gj["features"][7]["id"]
coordinates = gj["features"][7]["geometry"]["coordinates"]

# wgs84coord
a = Wgs84Coordinate(coordinates[0][0], coordinates[0][1])
b = Wgs84Coordinate(coordinates[1][0], coordinates[1][1])
c = Wgs84Coordinate(coordinates[2][0], coordinates[2][1])
d = Wgs84Coordinate(coordinates[3][0], coordinates[3][1])
# print(sheetnumber)
# print(a, b, c, d)

# pixelcoord
tl = sheet._mask.top_left
tr = sheet._mask.top_right
bl = sheet._mask.bottom_left
br = sheet._mask.bottom_right

# print(tl)

gcps = [ControlPoint(tl, a), ControlPoint(tr, b), ControlPoint(bl, c), ControlPoint(br, d)]

# georeference = Georeference(gcps)
#
# sheet.set_georeference(georeference)
# with open("test_10.8.json", 'w') as f:
#    f.write(sheet.to_annotationpage())
