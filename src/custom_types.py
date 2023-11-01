from dataclasses import dataclass

import numpy as np

# Custom name for the type of an OpenCV image. Technically its a numpy array of integers,
# but to make it more clear that it's an image we gave it a custom type name.
Cv2Image = np.ndarray

@dataclass
class PixelCoordinate:
    x: int
    y: int


@dataclass
class Wgs84Coordinate:
    lat: float
    lon: float


