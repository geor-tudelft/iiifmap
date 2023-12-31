from typing import TYPE_CHECKING
import requests


from ..custom_types import PixelCoordinate

class Mask:
    _coordinates: list["PixelCoordinate"]

    def __init__(self, coordinates: list["PixelCoordinate"]):
        self._coordinates = coordinates

    @classmethod
    def full_image(cls, image_endpoint: str) -> "Mask":
        info_url = image_endpoint + "/info.json"

        info_json = requests.get(info_url).json()
        width = info_json["width"]
        height = info_json["height"]

        top_left = PixelCoordinate(0, height)
        bottom_right = PixelCoordinate(width, 0)
        top_right = PixelCoordinate(width, height)
        bottom_left = PixelCoordinate(0, 0)

        return cls([bottom_left, top_left, top_right, bottom_right])


    @classmethod
    def from_svg_selector(cls, svg_selector: dict) -> "Mask":
        svg_value = svg_selector.get('value', '')

        points_str = svg_value.split('points="')[1].split('"')[0]
        points = points_str.split()

        coordinates = [PixelCoordinate(*map(int, point.split(','))) for point in points]

        if len(coordinates) == 4:
            return RectangleMask(coordinates)
        return cls(coordinates)

    def as_svg_selector(self) -> dict:
        width = max(coord.x for coord in self._coordinates)
        height = max(coord.y for coord in self._coordinates)
        points_str = " ".join(f"{coord.x},{coord.y}" for coord in self._coordinates)
        svg_value = f'<svg width="{width}" height="{height}"><polygon points="{points_str}" /></svg>'

        return {
            "type": "SvgSelector",
            "value": svg_value
        }

    def calculate_shape_quality(self) -> float:
        ...  # TODO


class RectangleMask(Mask):

    @classmethod
    def from_corners(
            cls,
            bottom_left: PixelCoordinate,
            top_left: PixelCoordinate,
            top_right: PixelCoordinate,
            bottom_right: PixelCoordinate
    ):
        self = cls([bottom_left, top_left, top_right, bottom_right])
        self._check_coordinate_order()
        return self

    @property
    def bottom_right(self):
        return self._coordinates[3]

    @property
    def top_right(self):
        return self._coordinates[2]

    @property
    def top_left(self):
        return self._coordinates[1]

    @property
    def bottom_left(self):
        return self._coordinates[0]

    def _check_coordinate_order(self):
        if self.bottom_left.x > self.bottom_right.x:
            raise ValueError("Bottom left x is bigger than bottom right x")
        if self.bottom_left.y > self.top_left.y:
            raise ValueError("Bottom left y is bigger than top left y")
        if self.bottom_right.y > self.top_right.y:
            raise ValueError("Bottom right y is bigger than top right y")
        if self.top_left.x > self.top_right.x:
            raise ValueError("Top left x is bigger than top right x")
