from src import MapSheet
from src.custom_types import Wgs84Coordinate
from src.georeference.baseclasses import ControlPoint, Georeference

with open(annotation_filename) as f:
    sheet = MapSheet.from_annotationpage(f.read())

top_left = sheet._mask.top_left
wgs84_co = Wgs84Coordinate(lat, lon)
gcp = ControlPoint(top_left, wgs84_co)

georeference = Georeference(list_of_controlpoints)
sheet.set_georeference(georeference)

with open(output_filename, 'w') as f:
    f.write(sheet.to_annotationpage())