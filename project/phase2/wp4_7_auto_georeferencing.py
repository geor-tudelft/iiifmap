from src import MapSeries
from src.georeference.matchfinder import get_georeference_from_mapsheet_matches

fieldminute_series = MapSeries.from_annotationpage_folder("/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/resources/tmk_field")
neatdrawings_series = MapSeries.from_annotationpage_folder("/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/resources/tmk_neat_combined")

for sheet in fieldminute_series.mapsheets:
    sheet_idx = sheet.metadata["sheet"]
    if sheet_idx != 32:
        continue

    neatdrawing = next(nsheet for nsheet in neatdrawings_series.mapsheets if nsheet.metadata["sheet"] == sheet_idx)

    georeferencing = get_georeference_from_mapsheet_matches(sheet, neatdrawing)