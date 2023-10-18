from ..custom_types import Cv2Image
from .baseclass import Mask


class MaskGenerator:
    maximum_corner_count: int

    def from_mapsheet(self, sheet_image: Cv2Image) -> Mask:
        ...  # TODO
