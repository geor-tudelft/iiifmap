from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..custom_types import Wgs84Coordinate
    from ..mapsheet import MapSheet
    from .baseclasses import Georeference
    from .referencemap import ReferenceMap


class GeoreferenceMatchFinder:
    reference_map: "ReferenceMap"

    def get_georeference_from_matches(
        self, mapsheet: "MapSheet", location_hint: "Wgs84Coordinate"
    ) -> "Georeference":
        ...
