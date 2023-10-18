from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..custom_types import PixelCoordinate


class Mask:
    _coordinates: list["PixelCoordinate"]

    @classmethod
    def from_svg(cls, svg: str) -> "Mask":
        ...  # TODO

    def to_svg(self) -> str:
        ...  # TODO

    def calculate_shape_quality(self) -> float:
        ...  # TODO
