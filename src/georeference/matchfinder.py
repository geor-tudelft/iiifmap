from typing import TYPE_CHECKING

import cv2
import numpy as np
from skimage import measure, transform

from extern.cnn_matching.lib.cnn_feature import cnn_feature_extract
from ..custom_types import Wgs84Coordinate, Cv2Image, PixelCoordinate
from .baseclasses import Georeference, ControlPoint
import logging

if TYPE_CHECKING:
    from ..mapsheet import MapSheet, Resolution

    from .referencemap import ReferenceMap

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

def _filter_matches_geometrically(matches: tuple[np.ndarray, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    # Code adapted from https://github.com/lan-cz/cnn-matching
    # LAN Chaozhen, LU Wanjie, YU Junming, XU Qing. Deep learning algorithm for feature matching of cross modality
    # remote sensing images[J]. Acta Geodaetica et Cartographica Sinica, 2021, 50(2): 189-202.

    _, inliers = measure.ransac(
        matches,
        transform.AffineTransform,
        min_samples=3,
        residual_threshold=_RESIDUAL_THRESHOLD,
        max_trials=1000,
    )
    inlier_idxs = np.nonzero(inliers)[0]
    return matches[0][inlier_idxs], matches[1][inlier_idxs]

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
    mapsheet_image = mapsheet.get_image(resolution=Resolution.MAX)
    reference_image = georeferenced_mapsheet.get_image(resolution=Resolution.MAX)

    matches = _find_matches(mapsheet_image, reference_image)
    matches_filtered = _filter_matches_geometrically(matches)
    controlpoints = _controlpoints_from_matches(matches_filtered, georeferenced_mapsheet._georeference)

    return Georeference(controlpoints)

def _get_refinement_box(matches: tuple[np.ndarray, np.ndarray], reference_georeference: "Georeference") -> tuple["Wgs84Coordinate", "Wgs84Coordinate"]:
    ... # TODO

class GeoreferenceMatchFinder:
    reference_map: "ReferenceMap"

    def get_georeference_from_reference_map(
        self, mapsheet: "MapSheet", location_hint: "Wgs84Coordinate"
    ) -> "Georeference":
        mapsheet_lowres = mapsheet.get_image(Resolution.percentage_size(LOWRES_PERCENTAGE))
        reference_lowres = ... # TODO
        reference_georeference = ... # TODO

        matches = _find_matches(mapsheet_lowres, reference_lowres)
        matches_filtered = _filter_matches_geometrically(matches)
        refinement_box = _get_refinement_box(matches_filtered, reference_georeference)

        mapsheet_highres = mapsheet.get_image(resolution=Resolution.MAX)
        reference_cropped_highres = ... # TODO
        reference_cropped_georeference = ...

        matches_refined = _find_matches(mapsheet_highres, reference_cropped_highres)
        matches_refined_filtered = _filter_matches_geometrically(matches_refined)

        controlpoints = _controlpoints_from_matches(matches_refined_filtered, reference_cropped_georeference)

        return Georeference(controlpoints)




