import os

from src import MapSeries

original = MapSeries.from_annotationpage_folder("/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/project/resources/tmk_field")

accepted_sheets = list([fn.replace(".json", "") for fn in os.listdir("results_ref")])
retried_sheets = list([fn.replace(".json", "")for fn in os.listdir("retries_final")])

total = len(original.mapsheets)
accepted = 0
retried = 0

for sheet in original.mapsheets:
    was_accepted = False
    for asheet in accepted_sheets:
        if asheet.startswith(sheet.id):
            was_accepted = True
            accepted += 1
            break

    was_retried = False
    for asheet in retried_sheets:
        if asheet.startswith(sheet.id):
            was_retried = True
            retried += 1
            break

print("total", total)
print("accepted", accepted)
print("retried", retried)
print("percent ", (accepted+retried) / total * 100)