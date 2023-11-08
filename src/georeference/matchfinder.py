import math
from typing import TYPE_CHECKING

import cv2
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from skimage import measure, transform

from extern.cnn_matching.lib.cnn_feature import cnn_feature_extract
from ..custom_types import Wgs84Coordinate, Cv2Image, PixelCoordinate
from .baseclasses import Georeference, ControlPoint
import logging

if TYPE_CHECKING:
    from ..mapsheet import MapSheet, Resolution

from .referencemap import ReferenceMap, SearchBox, ReferenceMapResolution

LOWRES_PERCENTAGE = 25
_RESIDUAL_THRESHOLD = 50 # todo

def _find_matches(image: "Cv2Image", reference_image: "Cv2Image") -> tuple[np.ndarray, np.ndarray]:
    # Code adapted from https://github.com/lan-cz/cnn-matching
    # LAN Chaozhen, LU Wanjie, YU Junming, XU Qing. Deep learning algorithm for feature matching of cross modality
    # remote sensing images[J]. Acta Geodaetica et Cartographica Sinica, 2021, 50(2): 189-202.


    kps_image, sco_image, des_image = cnn_feature_extract(image, nfeatures=-1)  # TODO test with feature filering
    kps_reference, sco_reference, des_reference = cnn_feature_extract(reference_image, nfeatures=-1)

    # Flann特征匹配
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=40)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_image, des_reference, k=2)

    goodMatch = []
    match_locations_on_image = []
    match_locations_on_reference = []

    # 匹配对筛选
    disdif_avg = 0
    # 统计平均距离差
    for m, n in matches:
        disdif_avg += n.distance - m.distance
    disdif_avg = disdif_avg / len(matches)

    for m, n in matches:
        # 自适应阈值
        if n.distance > m.distance + disdif_avg:
            goodMatch.append(m)
            p2 = cv2.KeyPoint(kps_reference[m.trainIdx][0], kps_reference[m.trainIdx][1], 1)
            p1 = cv2.KeyPoint(kps_image[m.queryIdx][0], kps_image[m.queryIdx][1], 1)
            match_locations_on_image.append([p1.pt[0], p1.pt[1]])
            match_locations_on_reference.append([p2.pt[0], p2.pt[1]])

    match_locations_on_image = np.array(match_locations_on_image)
    match_locations_on_reference = np.array(match_locations_on_reference)

    return match_locations_on_image, match_locations_on_reference

def _filter_matches_geometrically(matches: tuple[np.ndarray, np.ndarray], keep_best=-1) -> tuple[np.ndarray, np.ndarray]:
    # Code adapted from https://github.com/lan-cz/cnn-matching
    # LAN Chaozhen, LU Wanjie, YU Junming, XU Qing. Deep learning algorithm for feature matching of cross modality
    # remote sensing images[J]. Acta Geodaetica et Cartographica Sinica, 2021, 50(2): 189-202.

    model, inliers = measure.ransac(
        matches,
        transform.AffineTransform,
        min_samples=3,
        residual_threshold=_RESIDUAL_THRESHOLD,
        max_trials=1000,
    )

    inlier_idxs = np.nonzero(inliers)[0]
    matches_filtered = matches[0][inlier_idxs], matches[1][inlier_idxs]

    if keep_best != -1:
        residuals = model.residuals(matches_filtered[0], matches_filtered[1])
        sorted_idxs = np.argsort(residuals)[:keep_best]
        matches_filtered = (matches_filtered[0][sorted_idxs], matches_filtered[1][sorted_idxs])

    return matches_filtered

def _controlpoints_from_matches(matches: tuple[np.ndarray, np.ndarray], reference_georeference: "Georeference") -> list["ControlPoint"]:
    controlpoints = []
    for i in range(len(matches[0])):
        image_match = PixelCoordinate(*matches[0][i])
        reference_match = PixelCoordinate(*matches[1][i])
        reference_coordinate = reference_georeference.interpolate(reference_match)
        controlpoints.append(ControlPoint(image_match, reference_coordinate))

    return controlpoints


def get_georeference_from_mapsheet_matches(mapsheet: "MapSheet", georeferenced_mapsheet: "MapSheet") -> "Georeference":
    from src import Resolution
    PERC_MAPSHEET = 25
    mapsheet_image = mapsheet.get_image(resolution=Resolution.percentage_size(PERC_MAPSHEET))
    PERC_REF = 50
    reference_image = georeferenced_mapsheet.get_image(resolution=Resolution.percentage_size(PERC_REF))

    matches = _find_matches(mapsheet_image, reference_image)
    matches = (matches[0] * (100/PERC_MAPSHEET), matches[1] * (100/PERC_REF))
    matches_filtered = _filter_matches_geometrically(matches, keep_best=5)
    controlpoints = _controlpoints_from_matches(matches_filtered, georeferenced_mapsheet._georeference)

    return Georeference(controlpoints)

def get_georeference_from_mapsheet_template_matching(mapsheet: "MapSheet", mapsheet_scale: int, georeferenced_mapsheet: "MapSheet", georeferenced_mapsheet_scale: int) -> "Georeference":
    from ..mapsheet import Resolution

    scale_ratio = georeferenced_mapsheet_scale / mapsheet_scale
    resolution_correction = Resolution.percentage_size(int(100 / scale_ratio))
    mapsheet_res = resolution_correction if scale_ratio > 1 else Resolution.MAX
    reference_res = Resolution.MAX if scale_ratio > 1 else resolution_correction

    mapsheet_image = mapsheet.get_image(resolution=mapsheet_res)
    reference_image = georeferenced_mapsheet.get_image(resolution=reference_res)

    reference_mask = cv2.inRange(reference_image, (0, 0, 0), (10, 10, 10))  # Create a mask where black values are 0 and all others are 1
    reference_mask_inv = cv2.bitwise_not(reference_mask)  # Invert the mask so black becomes 255 and vice versa

    sample_edges = cv2.Canny(mapsheet_image, 100, 200)
    reference_edges = cv2.Canny(reference_image, 100, 200)

    # Use mask in template matching
    result = cv2.matchTemplate(sample_edges, reference_edges, cv2.TM_CCOEFF_NORMED, mask=reference_mask_inv)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    top_left = max_loc
    h, w = sample_edges.shape
    top_right = (top_left[0] + w, top_left[1])
    bottom_left = (top_left[0], top_left[1] + h)
    bottom_right = (top_left[0] + w, top_left[1] + h)

    pixel_coords = [PixelCoordinate(*top_left), PixelCoordinate(*top_right), PixelCoordinate(*bottom_left), PixelCoordinate(*bottom_right)]

    corrected_pixel_coords = []
    for px in pixel_coords:
        corrected_pixel_coords.append(PixelCoordinate(int(px.x * scale_ratio), int(px.y * scale_ratio)))

    wgs84_coords = [georeferenced_mapsheet._georeference.interpolate(pc) for pc in pixel_coords]

    controlpoints = [ControlPoint(pc, wc) for pc, wc in zip(corrected_pixel_coords, wgs84_coords)]

    return Georeference(controlpoints)



def _get_refinement_box(matches: tuple[np.ndarray, np.ndarray], reference_georeference: "Georeference") -> tuple["Wgs84Coordinate", "Wgs84Coordinate"]:
    ... # TODO

class GeoreferenceMatchFinder:
    reference_map: "ReferenceMap"

    def __init__(self, reference_map: "ReferenceMap", x_uncertainty_meters: float, y_uncertainty_meters):
        self.reference_map = reference_map
        self.x_uncertainty_meters = x_uncertainty_meters
        self.y_uncertainty_meters = y_uncertainty_meters

    def meters_to_degrees(self, x_meters: float, y_meters: float, latitude: float) -> tuple:
        # Constants for converting meters to degrees
        METERS_PER_DEGREE_LAT = 111139  # Approx. meters in a degree of latitude
        METERS_PER_DEGREE_LON = 111139 * math.cos(math.radians(latitude))  # Approx. meters in a degree of longitude at the given latitude

        x_degrees = x_meters / METERS_PER_DEGREE_LON
        y_degrees = y_meters / METERS_PER_DEGREE_LAT

        return x_degrees, y_degrees

    def get_georeference_from_reference_map(
        self, mapsheet: "MapSheet", location_hint: "Wgs84Coordinate"
    ) -> "Georeference":
        from src import Resolution

        mapsheet_lowres = mapsheet.get_image(Resolution.percentage_size(LOWRES_PERCENTAGE))

        x_degrees, y_degrees = self.meters_to_degrees(self.x_uncertainty_meters, self.y_uncertainty_meters, location_hint.lat)
        top = location_hint.lat + y_degrees
        bottom = location_hint.lat - y_degrees
        left = location_hint.lon - x_degrees
        right = location_hint.lon + x_degrees
        top_left = Wgs84Coordinate(top, left)
        bottom_right = Wgs84Coordinate(bottom, right)
        bottom_left = Wgs84Coordinate(bottom, left)
        top_right = Wgs84Coordinate(top, right)
        searchbox = SearchBox(top_left, bottom_right)
        reference_lowres = self.reference_map.extract_searchbox(searchbox, ReferenceMapResolution.LOW)
        reference_height, reference_width, _ = reference_lowres.shape

        cp_top_left = ControlPoint(PixelCoordinate(0, 0), top_left) # FIXME, doesn't account for tiles offset
        cp_bottom_right = ControlPoint(PixelCoordinate(reference_width, reference_height), bottom_right)
        cp_top_right = ControlPoint(PixelCoordinate(reference_width, 0), top_right)
        cp_bottom_left = ControlPoint(PixelCoordinate(0, reference_height), bottom_left)
        reference_georeference = Georeference([cp_bottom_left, cp_bottom_right, cp_top_right, cp_top_left])

        matches = _find_matches(mapsheet_lowres, reference_lowres)
        matches_filtered = _filter_matches_geometrically(matches, keep_best=30)

        self.plot(mapsheet_lowres, matches_filtered, reference_lowres)

        # res_corrected_matches = []
        # for img_match in matches_filtered[0]:

        scale_factor = 100/LOWRES_PERCENTAGE
        matches_resolution_corrected = (matches_filtered[0] * scale_factor, matches_filtered[1])

        #refinement_box = _get_refinement_box(matches_filtered, reference_georeference)

        #mapsheet_highres = mapsheet.get_image(resolution=Resolution.MAX)
        #reference_cropped_highres = ... # TODO
        #reference_cropped_georeference = ...

        #matches_refined = _find_matches(mapsheet_highres, reference_cropped_highres)
        #matches_refined_filtered = _filter_matches_geometrically(matches_refined)

        controlpoints = _controlpoints_from_matches(matches_resolution_corrected, reference_georeference)

        return Georeference(controlpoints)

    def plot(self, mapsheet_lowres, matches_filtered, reference_lowres):
        src_pts = np.float32(matches_filtered[0]).reshape(-1, 1, 2)
        dst_pts = np.float32(matches_filtered[1]).reshape(-1, 1, 2)
        # Compute the affine transformation matrix
        M, _ = cv2.estimateAffine2D(src_pts, dst_pts)

        if M is None:
            print("Couldn't estimate an affine transformation.")
            return

        warped_mapsheet = cv2.warpAffine(mapsheet_lowres, M, (reference_lowres.shape[1], reference_lowres.shape[0]))
        mask = cv2.cvtColor(warped_mapsheet, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)

        # Use the mask to combine the images
        overlay = reference_lowres.copy()
        for c in range(0, 3):  # Assuming a 3-channel image (BGR)
            overlay[:, :, c] = np.where(mask == 255, warped_mapsheet[:, :, c], reference_lowres[:, :, c])

        # Convert to PIL Image and display
        img = Image.fromarray(overlay)
        img.show()
