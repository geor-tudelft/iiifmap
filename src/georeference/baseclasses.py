from ..custom_types import PixelCoordinate, Wgs84Coordinate


class ControlPoint:
    pixel_coordinate = PixelCoordinate
    wgs84_coordinate = Wgs84Coordinate


class Georeference:
    control_points: list["ControlPoint"]

    @classmethod
    def from_json(cls, json_data: str) -> "Georeference": ...

    def to_json(self) -> str: ...

    def refine(self) -> str: ...
