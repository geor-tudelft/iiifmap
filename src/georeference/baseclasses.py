from ..custom_types import PixelCoordinate, Wgs84Coordinate
from typing import Dict, List
from numpy.linalg import lstsq
import numpy as np


class ControlPoint:
    pixel_coordinate: PixelCoordinate
    wgs84_coordinate: Wgs84Coordinate

    def __init__(self, pixel_coordinate: PixelCoordinate, wgs84_coordinate: Wgs84Coordinate):
        self.pixel_coordinate = pixel_coordinate
        self.wgs84_coordinate = wgs84_coordinate

    @classmethod
    def from_geojson_feature(cls, feature: Dict) -> "ControlPoint":
        pixel_coords = PixelCoordinate(*feature["properties"]["pixelCoords"])
        coordinates = Wgs84Coordinate(*feature["geometry"]["coordinates"])
        return cls(pixel_coords, coordinates)

    def as_geojson_feature(self) -> Dict:
        return {
            "type": "Feature",
            "properties": {
                "pixelCoords": [self.pixel_coordinate.x, self.pixel_coordinate.y]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [self.wgs84_coordinate.lon, self.wgs84_coordinate.lat]
            }
        }


class Georeference:
    control_points: list["ControlPoint"]

    def __init__(self, control_points: List["ControlPoint"]):
        self.control_points = control_points

    @classmethod
    def from_geojson_dict(cls, geojson_dict: Dict) -> "Georeference":
        features = geojson_dict["features"]
        control_points = [ControlPoint.from_geojson_feature(feature) for feature in features]
        return cls(control_points)

    def as_geojson_dict(self) -> Dict:
        return {
            "type": "FeatureCollection",
            "transformation": {
                "type": "polynomial",
                "options": {
                    "order": 1
                }
            },
            "features": [control_point.as_geojson_feature() for control_point in self.control_points]
        }

    def refine(self) -> str: ...

    def _prepare_interpolation(self):
        A = []
        B = []
        for cp in self.control_points:
            px, py = cp.pixel_coordinate.x, cp.pixel_coordinate.y
            lat, lon = cp.wgs84_coordinate.lat, cp.wgs84_coordinate.lon
            A.append([px, py, 1, 0, 0, 0])
            A.append([0, 0, 0, px, py, 1])
            B.extend([lat, lon])

        A = np.array(A)
        B = np.array(B)
        self.transformation_matrix, _, _, _ = lstsq(A, B, rcond=None)

    def interpolate(self, pixel_coordinate: PixelCoordinate) -> Wgs84Coordinate:
        if not hasattr(self, 'transformation_matrix'):
            self._prepare_interpolation()

        x, y = pixel_coordinate.x, pixel_coordinate.y
        a, b, c, d, e, f = self.transformation_matrix

        lat = a * x + b * y + c
        lon = d * x + e * y + f

        return Wgs84Coordinate(lat, lon)