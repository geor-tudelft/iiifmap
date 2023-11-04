import os

from src import MapSeries, MapSheet

final = MapSeries.from_annotationpage_folder("results_final")
with open("progress.json", "w") as f:
    f.write(final.to_annotationpage())

best_file = None
best_scale = 1000
last_sheet_name = ""
for file in os.listdir("retries_final"):
    if not file.endswith(".json"):
        continue
    sheet_name = file.split("_")[0]
    if sheet_name != last_sheet_name and best_file:
        final.mapsheets.append(best_file)
        best_scale = 1000

    with open(os.path.join("retries_final", file), "r") as f:
        sheet = MapSheet.from_annotationpage(f.read())

    scale = sheet._georeference.scale_inaccuracy(25000, 300)
    if abs(scale) < best_scale:
        best_file = sheet
        best_scale = abs(scale)


final.mapsheets.append(best_file)

with open("progress_full2.json", "w") as f:
    f.write(final.to_annotationpage())

refmap = MapSeries.from_annotationpage_folder("results_refmap")
sheets_to_remove = []
for sheet in refmap.mapsheets:
    if abs(sheet._georeference.scale_inaccuracy(25000, 300))>10:
        sheets_to_remove.append(sheet)

for sheet in sheets_to_remove:
    refmap.mapsheets.remove(sheet)

with open("progress_refmap_filtered.json", "w") as f:
    f.write(refmap.to_annotationpage())