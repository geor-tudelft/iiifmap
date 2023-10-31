from src import MapSheet
from src.custom_types import Wgs84Coordinate
from src.georeference.baseclasses import ControlPoint, Georeference
from typing import Dict, List
import json

with open(r"F:\TU\GEO1016\Git\iiifmap\project\resources\bonnebladen\10.8.json") as f:
    sheet = MapSheet.from_annotationpage(f.read())


class Coordinate_Array:
    a = Wgs84Coordinate
    b = Wgs84Coordinate
    c = Wgs84Coordinate
    d = Wgs84Coordinate

    def __init__(self, a: Wgs84Coordinate, b: Wgs84Coordinate, c: Wgs84Coordinate, d: Wgs84Coordinate):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    @classmethod
    def from_geojson_feature_multipoint(cls, feature: Dict) -> "Coordinate_Array":
        coordinates = Coordinate_Array(*feature["features"][8]["geometry"]["coordinates"])
        return cls(coordinates)


with open(r"F:\TU\GEO1016\Git\iiifmap\project\phase1\results_wp1\WGS84coordsBBlad.geojson") as f:
    # wgs84 = ControlPoint.wgs84_coordinate(f.read())
    feature = Dict
    wgs84 = json.dumps(feature['features'][8])

print(wgs84)
tl = sheet._mask.top_left
tr = sheet._mask.top_right
br = sheet._mask.bottom_right
bl = sheet._mask.bottom_left

# wgs84_co = Wgs84Coordinate(lat, lon)
# gcp = ControlPoint(top_left, wgs84_co)
#
# georeference = Georeference(list_of_controlpoints)
# sheet.set_georeference(georeference)
#
# with open(output_filename, 'w') as f:
#     f.write(sheet.to_annotationpage())
