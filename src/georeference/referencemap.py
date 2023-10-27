from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import MapSheet
    from ..custom_types import Wgs84Coordinate, Cv2Image


class SearchBoxGenerator:
    # parameters needed for searchbox arithmetic

    @classmethod
    def from_mapsheet(cls, mapsheet: "MapSheet") -> "SearchBox": ...


class SearchBox:
    top_left = "Wgs84Coordinate"
    bottom_right = "Wgs84Coordinate"


class ReferenceMap:
    _wms_link: str # Or should it be IIIF presentation?

    def extract_searchbox(self, searchbox: "SearchBox") -> "Cv2Image": ...