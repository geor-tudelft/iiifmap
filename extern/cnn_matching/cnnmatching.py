import argparse
import json
import time
from io import BytesIO

import cv2
import imageio
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
from skimage import measure, transform
from numpy.polynomial.polynomial import Polynomial
from scipy.ndimage import map_coordinates

import plotmatch
from lib.cnn_feature import cnn_feature_extract

# time count
start = time.perf_counter()

_RESIDUAL_THRESHOLD = 100
PERCENTAGE = 100
NO_FEATURES = -1
# Test1nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8


# Function to apply polynomial transformation
def polynomial_transform(image, x_poly, y_poly, output_shape):
    h, w, c = output_shape
    x_indices, y_indices = np.meshgrid(np.arange(w), np.arange(h))

    # Convert meshgrid to polynomial input shape
    flat_x_indices = x_indices.flatten()
    flat_y_indices = y_indices.flatten()

    # Transform coordinates using polynomial
    transformed_x_indices = x_poly(flat_x_indices)
    transformed_y_indices = y_poly(flat_y_indices)

    # Clip coordinates to image dimensions
    transformed_x_indices = np.clip(transformed_x_indices, 0, w - 1)
    transformed_y_indices = np.clip(transformed_y_indices, 0, h - 1)

    # Reshape to meshgrid shape
    transformed_x_indices = transformed_x_indices.reshape((h, w))
    transformed_y_indices = transformed_y_indices.reshape((h, w))

    coordinates = np.array([transformed_y_indices, transformed_x_indices])
    transformed_image = np.zeros(output_shape, dtype=image.dtype)

    for i in range(c):
        transformed_image[:, :, i] = map_coordinates(
            image[:, :, i], coordinates, order=1, mode="nearest"
        )

    return transformed_image


def draw_lines_on_composite(composite, orig_points, new_points, color=(0, 255, 0)):
    color_origin = (255, 0, 0)  # Blue for origin
    color_end = (0, 0, 255)  # Red for end
    for pt1, pt2 in zip(orig_points, new_points):
        x1, y1 = tuple(map(int, pt1))
        x2, y2 = tuple(map(int, pt2))
        cv2.line(composite, (x1, y1), (x2, y2), color, 1)
        cv2.circle(composite, (x1, y1), 1, color_origin, -1)
        cv2.circle(composite, (x2, y2), 1, color_end, -1)


class Match:
    loc_left: tuple[float, float]
    loc_right: tuple[float, float]

    def __init__(self, loc_left, loc_right) -> None:
        self.loc_left = loc_left
        self.loc_right = loc_right


def find_matches(image1, features_image_2):
    t = time.perf_counter()
    kps_left, sco_left, des_left = cnn_feature_extract(image1, nfeatures=NO_FEATURES)
    print("Kp1: {} s".format(time.perf_counter() - t))
    t = time.perf_counter()

    kps_right, sco_right, des_right = features_image_2
    print("Kp2: {} s".format(time.perf_counter() - t))

    t = time.perf_counter()
    # Flann特征匹配
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=40)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_left, des_right, k=2)
    print("knnmatch: {} s".format(time.perf_counter() - t))
    t = time.perf_counter()
    goodMatch = []
    locations_1_to_use = []
    locations_2_to_use = []

    # 匹配对筛选
    min_dist = 1000
    max_dist = 0
    disdif_avg = 0
    # 统计平均距离差
    for m, n in matches:
        disdif_avg += n.distance - m.distance
    disdif_avg = disdif_avg / len(matches)

    for m, n in matches:
        # 自适应阈值
        if n.distance > m.distance + disdif_avg:
            goodMatch.append(m)
            p2 = cv2.KeyPoint(kps_right[m.trainIdx][0], kps_right[m.trainIdx][1], 1)
            p1 = cv2.KeyPoint(kps_left[m.queryIdx][0], kps_left[m.queryIdx][1], 1)
            locations_1_to_use.append([p1.pt[0], p1.pt[1]])
            locations_2_to_use.append([p2.pt[0], p2.pt[1]])
    # goodMatch = sorted(goodMatch, key=lambda x: x.distance)
    print("match num is %d" % len(goodMatch))
    locations_1_to_use = np.array(locations_1_to_use)
    locations_2_to_use = np.array(locations_2_to_use)

    print("Location finding: {} s".format(time.perf_counter() - t))
    t = time.perf_counter()

    _, inliers1 = measure.ransac(
        (locations_1_to_use, locations_2_to_use),
        transform.AffineTransform,
        min_samples=3,
        residual_threshold=_RESIDUAL_THRESHOLD,
        max_trials=1000,
    )

    inlier_idxs1 = np.nonzero(inliers1)[0]

    # Perform geometric verification using RANSAC on the first inliers.
    _, inliers2 = measure.ransac(
        (locations_1_to_use[inlier_idxs1], locations_2_to_use[inlier_idxs1]),
        transform.AffineTransform,
        min_samples=3,
        residual_threshold=20,
        max_trials=1000,
    )

    print("Ransac: {} s".format(time.perf_counter() - t))

    # Update inlier indices based on the second RANSAC iteration
    final_inlier_idxs = inlier_idxs1[inliers2]

    print("Found %d inliers" % len(final_inlier_idxs))

    for idx in final_inlier_idxs:
        yield Match(locations_1_to_use[idx], locations_2_to_use[idx])


def read_image_from_iiif(url, percentage=25):
    response = requests.get(url + f"/full/pct:{percentage}/0/default.jpg")
    if response.status_code == 200:  # OK
        image = Image.open(BytesIO(response.content))
        return np.array(image)
    else:
        print("Failed to download image")
        return None


with open("tmk.json", "r") as f:
    full_json = json.load(f)

sheet = next(sheet for sheet in full_json if sheet["title"] == "Amersfoort")
reference_link = sheet["nettekeningen"][0]["images"][0]
reference_img = read_image_from_iiif(reference_link, percentage=PERCENTAGE)

#reference_link = "/Users/ole/Library/Mobile Documents/com~apple~CloudDocs/Areas/Geomatics/Synthesis/iiifmap/prototype_data/amersfoort_test/target/Screenshot_Safari_000589.png"
#reference_img = np.array(Image.open(reference_link))[:,:,:3]
reference_features = cnn_feature_extract(reference_img, nfeatures=-1)

composite = np.zeros_like(reference_img)
i = 0
for veldminuut in sheet["veldminuten"]:
    print("Parsing")
    image_link = veldminuut["images"][0]
    t = time.perf_counter()
    image = read_image_from_iiif(image_link, percentage=PERCENTAGE)
    print("Image load: {} s".format(time.perf_counter() - t))

    t = time.perf_counter()
    matches = list(find_matches(image, reference_features))
    print("Find matches: {} s".format(time.perf_counter() - t))

    pts_left = np.float32([m.loc_left for m in matches])
    pts_right = np.float32([m.loc_right for m in matches])

    # POLY

    x_poly = Polynomial.fit(pts_left[:, 0], pts_right[:, 0], 1)
    y_poly = Polynomial.fit(pts_left[:, 1], pts_right[:, 1], 1)

    # Transform points
    transformed_pts_left = np.zeros_like(pts_left)
    transformed_pts_left[:, 0] = x_poly(pts_left[:, 0])
    transformed_pts_left[:, 1] = y_poly(pts_left[:, 1])

    transformed_pts_left = np.zeros_like(pts_left)
    transformed_pts_left[:, 0] = x_poly(pts_left[:, 0])
    transformed_pts_left[:, 1] = y_poly(pts_left[:, 1])

    print("X polynomial coefficients:", x_poly.coef)
    print("Y polynomial coefficients:", y_poly.coef)

    output_shape = reference_img.shape
    #transformed_image = polynomial_transform(image, x_poly, y_poly, output_shape)

    #composite += transformed_image  # Replace this with your desired composite operation

    # Compute the affine matrix
    affine_matrix, _ = cv2.estimateAffine2D(pts_left, pts_right)

    # Transform the original points to their new locations on the composite image
    transformed_pts_left = cv2.transform(np.array([pts_left]), affine_matrix[:2])[0]

    # Draw lines on the composite image

    # Apply the affine transformation to update the composite
    rows, cols, _ = reference_img.shape
    composite += cv2.warpAffine(image, affine_matrix[:2], (cols, rows))

    draw_lines_on_composite(composite, transformed_pts_left, pts_right)

    i += 1
    break


cv2.imwrite("result_ai_full6.png", cv2.cvtColor(composite, cv2.COLOR_RGB2BGR))

# Display the images using matplotlib
plt.figure()
img = Image.fromarray(composite)
img.show()
