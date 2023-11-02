import geojson

from src import mapseries
from src.custom_types import Wgs84Coordinate
from src.georeference.baseclasses import ControlPoint, Georeference


# class CoordinateArray:
#     _coordinates: list["Wgs84Coordinate"]
#     sheetnumber: int
#     def __init__(self, coordinates: list["Wgs84Coordinate"], sheetnumber: int):
#         self._coordinates = coordinates
#         self.sheetnumber = sheetnumber
#
#     def from_geojson_Multipoint(self, gjson) -> "CoordinateArray":
#         #ToDo
#         return self(sheetnumber, coordinates)
#     def a(self):
#        return self._coordinates[0]
#     def b(self):
#        return self._coordinates[1]
#     def c(self):
#        return self._coordinates[2]
#     def d(self):
#        return self._coordinates[3]

# with open(r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\resources\bonnebladen\10.8.json") as f:
#     sheet = MapSheet.from_annotationpage(f.read())


d_bonnebladen = r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\resources\bonnebladen"
d_tmk_neat_combined = r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\resources\tmk_neat_combined"

directory = d_bonnebladen
target_directory = "results_wp3/bonnebladen/"

mapseries = mapseries.MapSeries.from_annotationpage_folder(directory)
sheets = mapseries.mapsheets
for sheet in sheets:
    sheetn = sheet.metadata["sheet"]
    # pixelcoord
    tl = sheet._mask.top_left
    tr = sheet._mask.top_right
    bl = sheet._mask.bottom_left
    br = sheet._mask.bottom_right

    if directory == d_bonnebladen:
        coordsource = r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\phase1\results_wp1\WGS84coordsBBlad.geojson"
    if directory == d_tmk_neat_combined:
        coordsource = r"C:\Users\ribar\Documents\TU\Synthesis\iiifmap\project\phase1\results_wp1\WGS84coordsTMK.geojson"
    else:
        print("no valid directory and/or coordinate source")



    with open(coordsource) as f:
        gj = geojson.load(f)
    sheetnumber = gj["features"][sheetn-1]["id"]
    if sheetn == sheetnumber:
        coordinates = gj["features"][sheetn-1]["geometry"]["coordinates"]
        # wgs84coord
        a = Wgs84Coordinate(coordinates[0][1], coordinates[0][0])
        b = Wgs84Coordinate(coordinates[1][1], coordinates[1][0])
        c = Wgs84Coordinate(coordinates[2][1], coordinates[2][0])
        d = Wgs84Coordinate(coordinates[3][1], coordinates[3][0])

        gcps = [ControlPoint(tl, a), ControlPoint(tr, b), ControlPoint(bl, c), ControlPoint(br, d)]

        georeference = Georeference(gcps)

        sheet.set_georeference(georeference)
        with open(target_directory+sheet.id+".json", 'w') as g:
           g.write(sheet.to_annotationpage())

    else:
        print(sheet.id + " for this sheet " + str(sheetn) + " and " + str(sheetnumber) + " do not match")

print("directory used: "+ directory + " coordinate source used: " + coordsource + "annotations placed in" + target_directory)