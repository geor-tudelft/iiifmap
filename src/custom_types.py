import numpy as np

# Custom name for the type of an OpenCV image. Technically its a numpy array of integers,
# but to make it more clear that it's an image we gave it a custom type name.
Cv2Image = np.ndarray


class PixelCoordinate:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Wgs84Coordinate:
    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon
