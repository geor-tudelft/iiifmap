from ..custom_types import PixelCoordinate, Wgs84Coordinate


class ControlPoint:
    pixel_coordinate = PixelCoordinate
    wgs84_coordinate = Wgs84Coordinate


class Georeference:
    control_points: list["ControlPoint"]

    @classmethod
    def from_geojson_dict(cls, geojson_dict: dict) -> "Georeference": ...

    def as_geojson_dict(self) -> dict: ...

    def refine(self) -> str: ...
