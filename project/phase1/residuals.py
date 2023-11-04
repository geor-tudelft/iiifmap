import logging
import os
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from logger_config import setup_logging
from src import MapSeries
from src.custom_types import PixelCoordinate, Wgs84Coordinate

setup_logging("residuals_phase1.log")

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent

with open(os.path.join(PROJECT_ROOT, "resources", "reference churches.csv"), "r") as f:
    lines = f.readlines()

lines.pop(0) # Remove header

export_lines = ["series;sheet;pixel x;pixel y; wgs84 lat;wgs84 lon;place;interpolated lat;interpolated lon;residual meters\n"]

bonnebladen_path = os.path.join(PROJECT_ROOT, "phase1", "results_wp3", "bonnebladen", "no mask", "FULL_bonnebladen_nomask.json")
with open(bonnebladen_path, "r") as f:
    bonnebladen_series = MapSeries.from_annotationpage(f.read())

tmk_neat_path = os.path.join(PROJECT_ROOT, "phase1", "results_wp3", "tmk_neat_combined", "with mask", "FULL_tmk_neat_combined.json")
with open(tmk_neat_path, "r") as f:
    tmk_neat_series = MapSeries.from_annotationpage(f.read())

field = MapSeries.from_annotationpage_folder("../phase2/results_refmap")

residuals = []

for line in lines:
    series_name, sheet_num, x, y, lat, lon, *_, place = line.split(";")
    if series_name == "TMK":
        series = tmk_neat_series
    elif series_name == "Bonne":
        series = bonnebladen_series
    else:
        series = field

    sheet = next((s for s in series.mapsheets if s.metadata["sheet"] == int(sheet_num)), None)
    if not sheet:
        logging.error(f"Could not find {series_name} sheet {sheet_num}. Residuals could not be calculated for {place}.")
        continue

    interpolated_coords = sheet._georeference.interpolate(PixelCoordinate(int(x), int(y)))
    residual = Wgs84Coordinate(float(lat), float(lon)).haversine_distance(interpolated_coords)
    residuals.append((series_name, residual))
    logging.info(f"Residual for {series_name} {place}: {residual} m")

    row = [
        series_name, sheet_num, x, y, lat, lon, place.strip(), f"{interpolated_coords.lat:5f}", f"{interpolated_coords.lon:5f}", str(int(residual))
    ]
    export_lines.append(";".join(map(str, row))+"\n")

with open("residuals_field.csv", "w") as f:
    f.writelines(export_lines)


# tmk_residuals = [residual for series, residual in residuals if series == 'TMK']
# bonne_residuals = [residual for series, residual in residuals if series == 'Bonne']
#
# num_bins = 50
# min_exponent = np.floor(np.log10(min(tmk_residuals + bonne_residuals)))
# max_exponent = np.ceil(np.log10(max(tmk_residuals + bonne_residuals)))
# bins = np.logspace(min_exponent, max_exponent, num_bins)
#
# plt.figure(figsize=(10, 6))
# plt.hist(tmk_residuals, bins=bins, color='blue', alpha=0.7, edgecolor='black', log=True)
# plt.xscale('log')
# plt.title('Residual Distribution for TMK Series')
# plt.xlabel('Residual (meters)')
# plt.ylabel('Frequency')
# plt.grid(axis='y', alpha=0.75)
# plt.savefig('tmk_residuals_histogram.png')
# plt.show()
#
# plt.figure(figsize=(10, 6))
# plt.hist(bonne_residuals, bins=bins, color='green', alpha=0.7, edgecolor='black', log=True)
# plt.xscale('log')
# plt.title('Residual Distribution for Bonne Series')
# plt.xlabel('Residual (meters)')
# plt.ylabel('Frequency')
# plt.grid(axis='y', alpha=0.75)
# plt.savefig('bonne_residuals_histogram.png')
# plt.show()