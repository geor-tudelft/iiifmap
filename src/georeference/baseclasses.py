from ..custom_types import PixelCoordinate, Wgs84Coordinate
from typing import Dict, List


class ControlPoint:
    pixel_coordinate = PixelCoordinate
    wgs84_coordinate = Wgs84Coordinate

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
                "coordinates": [self.wgs84_coordinate.lat, self.wgs84_coordinate.lon]
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
