import math

from ..custom_types import PixelCoordinate, Wgs84Coordinate
from typing import Dict, List
from numpy.linalg import lstsq
import numpy as np


class ControlPoint:
    pixel_coordinate: PixelCoordinate
    wgs84_coordinate: Wgs84Coordinate

    def __init__(self, pixel_coordinate: PixelCoordinate, wgs84_coordinate: Wgs84Coordinate):
        self.pixel_coordinate = pixel_coordinate
        self.wgs84_coordinate = wgs84_coordinate

    @classmethod
    def from_geojson_feature(cls, feature: Dict) -> "ControlPoint":
        pixel_coords = PixelCoordinate(*feature["properties"]["pixelCoords"])
        coordinates = Wgs84Coordinate(feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
        return cls(pixel_coords, coordinates)

    def as_geojson_feature(self) -> Dict:
        return {
            "type": "Feature",
            "properties": {
                "pixelCoords": [self.pixel_coordinate.x, self.pixel_coordinate.y]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [self.wgs84_coordinate.lon, self.wgs84_coordinate.lat]
            }
        }


def euclidean_distance(p1, p2):
    """Compute the Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def compute_image_distance(pixel_distance, scale, dpi):
    """Convert pixel distance to real-world distance in kilometers using map's scale and dpi."""
    inches_per_pixel = 1 / dpi
    real_distance = pixel_distance * inches_per_pixel  # in inches
    # Convert inches to meters
    real_distance_m = real_distance * 0.0254
    # Convert to the distance on the ground using the scale
    return (real_distance_m * scale) / 1000  # in kilometers


def percentage_difference(georef_distance, image_distance):
    """Compute the percentage difference between two distances."""
    return abs((georef_distance - image_distance) / image_distance) * 100

def latlon_distance(coord1, coord2):
    """Compute the approximate distance between two lat-lon coordinates in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    delta_lat = lat2 - lat1
    delta_lon = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(delta_lat**2 + delta_lon**2) * 111.32



class Georeference:
    control_points: list["ControlPoint"]

    def __init__(self, control_points: List["ControlPoint"]):
        self.control_points = control_points

    @classmethod
    def from_geojson_dict(cls, geojson_dict: Dict) -> "Georeference":
        features = geojson_dict["features"]
        control_points = [ControlPoint.from_geojson_feature(feature) for feature in features]
        return cls(control_points)

    def as_geojson_dict(self) -> Dict:
        return {
            "type": "FeatureCollection",
            "transformation": {
                "type": "polynomial",
                "options": {
                    "order": 1
                }
            },
            "features": [control_point.as_geojson_feature() for control_point in self.control_points]
        }

    def refine(self) -> str: ...

    @property
    def transformation_matrix(self) -> np.ndarray:
        if not hasattr(self, '_transformation_matrix'):
            self._transformation_matrix = self._prepare_interpolation()

        return self._transformation_matrix

    def _prepare_interpolation(self) -> np.ndarray:
        A = []
        B = []
        for cp in self.control_points:
            px, py = cp.pixel_coordinate.x, cp.pixel_coordinate.y
            lat, lon = cp.wgs84_coordinate.lat, cp.wgs84_coordinate.lon
            A.append([px, py, 1, 0, 0, 0])
            A.append([0, 0, 0, px, py, 1])
            B.extend([lat, lon])

        A = np.array(A)
        B = np.array(B)
        transformation_matrix, _, _, _ = lstsq(A, B, rcond=None)

        return transformation_matrix

    def interpolate(self, pixel_coordinate: PixelCoordinate) -> Wgs84Coordinate:
        x, y = pixel_coordinate.x, pixel_coordinate.y
        a, b, c, d, e, f = self.transformation_matrix

        lat = a * x + b * y + c
        lon = d * x + e * y + f

        return Wgs84Coordinate(lat, lon)

    def jacobian_determinant(self) -> float:
        a, b, _, d, e, _ = self.transformation_matrix
        return a * e - b * d  # determinant of a 2x2 matrix

    def shear_factor(self) -> float:
        a, b, _, d, e, _ = self.transformation_matrix
        scale_x = (a**2 + d**2)**0.5  # magnitude of the first column
        scale_y = (b**2 + e**2)**0.5  # magnitude of the second column
        dot_product = a * b + d * e  # dot product of columns
        cosine = dot_product / (scale_x * scale_y)  # cosine of angle between columns
        return cosine

    def scale_inaccuracy(self, scale: float, dpi: float) -> float:
        total_percentage_diff = 0
        num_pairs = 0

        # Iterating over every pair of control points
        for i, cp1 in enumerate(self.control_points):
            for j, cp2 in enumerate(self.control_points):
                if i < j:  # Avoid computing for same pair twice
                    pixel_dist = euclidean_distance(
                        (cp1.pixel_coordinate.x, cp1.pixel_coordinate.y),
                        (cp2.pixel_coordinate.x, cp2.pixel_coordinate.y)
                    )
                    image_dist_km = compute_image_distance(pixel_dist, scale, dpi)  # this will be in inches

                    georef_dist_km = latlon_distance(
                        (cp1.wgs84_coordinate.lat, cp1.wgs84_coordinate.lon),
                        (cp2.wgs84_coordinate.lat, cp2.wgs84_coordinate.lon)
                    )
                    total_percentage_diff += percentage_difference(georef_dist_km, image_dist_km)
                    num_pairs += 1

        return total_percentage_diff / num_pairs
