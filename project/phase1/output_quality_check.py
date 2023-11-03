"""
Script to calculate the distance between
the corresponding points
of the manual and automatic masks.
Reports the results in a distance.csv file.
"""

import os
import math
import cv2 as cv
import numpy as np
from src.custom_types import PixelCoordinate
from src import MapSeries
from src import RectangleMask
from pathlib import Path


def order_points(points: list[PixelCoordinate]) -> list[PixelCoordinate]:
    """
    Order points of the masks clockwise starting from the top left corner
    """
    center = PixelCoordinate(sum([p.x for p in points]) / len(points),
                             sum([p.y for p in points]) / len(points))

    def sort_key(p: PixelCoordinate) -> float:
        return math.atan2(p.y - center.y, p.x - center.x)

    return sorted(points, key=sort_key)


def distance_euclidean(p1: PixelCoordinate, p2: PixelCoordinate) -> float:
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


DIRECTORY = Path(__file__).parent.parent  # to go to iiifmap/project directory

"""Flag to write the report"""
write_report = False  # Set to True to write the report


# Initialize the report
if write_report:
    report = open(os.path.join(DIRECTORY, "resources", "distance.csv"), 'w')
    print(f"\n+The report will be written in {report.name}+\n")
    report.write("sheetnumber, distance0, distance1, distance2, distance3\n")

# Load the manual and automatic masks
fm = open(os.path.join(DIRECTORY, "resources", "manual_tmk_masks.json"), 'r').read()
manual_series = MapSeries.from_annotationpage(fm)
auto_series = MapSeries.from_annotationpage_folder(os.path.join(DIRECTORY, "phase1", "results_wp2", "tmk_neat_combined"))


# Compare the masks
print(f"Number of manually generated masks: {len(manual_series.mapsheets)}")
print(f"Number of auto-generated masks: {len(auto_series.mapsheets)}\n")
i = 0  # Counter for matches
for sheet_manu in manual_series.mapsheets:
    manu_id = sheet_manu._image_endpoint.split('/')[-1]
    for sheet_auto in auto_series.mapsheets:
        # print(sheet_auto._image_endpoint)
        auto_id = sheet_auto._image_endpoint.split('/')[-1]
        if manu_id == auto_id and isinstance(sheet_manu.mask, RectangleMask):
            image = sheet_manu.get_image()
            i += 1
            a = order_points(sheet_manu.mask._coordinates)
            b = order_points(sheet_auto.mask._coordinates)

            # calculate the distance between the points
            dist0 = distance_euclidean(a[0], b[0])
            dist1 = distance_euclidean(a[1], b[1])
            dist2 = distance_euclidean(a[2], b[2])
            dist3 = distance_euclidean(a[3], b[3])

            # Draw mask on image

            if write_report:
                pts_a = np.array([[a[0].x, a[0].y], [a[1].x,a[1].y], [a[2].x,a[2].y], [a[3].x,a[3].y]], np.int32)
                pts_a = pts_a.reshape((-1, 1, 2))
                pts_b = np.array([[b[0].x, b[0].y], [b[1].x,b[1].y], [b[2].x,b[2].y], [b[3].x,b[3].y]], np.int32)
                pts_b = pts_b.reshape((-1, 1, 2))
                cv.polylines(image, [pts_a], True, (30,129,176), 8)  # blue color for manual mask
                cv.polylines(image, [pts_b], True, (226,135,67), 8)  # orange color for auto mask
                cv.imwrite(fr'C:\Users\VoL\Desktop\images\{manu_id[:-4]}.png', image)
                report.write(f"{manu_id}, {dist0}, {dist1}, {dist2}, {dist3}\n")
        elif manu_id == auto_id and not isinstance(sheet_manu.mask, RectangleMask):
            print(f"Mask for {manu_id} is not a rectangle")
            continue
print(f"\nTotal number of matching map sheets: {i}")
