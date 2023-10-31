from io import BytesIO
from typing import TYPE_CHECKING, Any, Union

import numpy as np
import requests
from PIL import Image
import json

from matplotlib import pyplot as plt

from .mask.baseclass import RectangleMask
if TYPE_CHECKING:
    from .custom_types import Cv2Image

from .georeference import Georeference
from .mask import Mask

# Constants
AUTO = 0


class Resolution:
    """Class used for convenience while getting mapsheet images at diferent resolutions.

    It doesn't actually do anything, it's just for making it easier to handle
    the different resolution options, since the IIIF image API can be a bit unclear.

    When a function/method asks for a resolution, use this class.

    When you want maximum resolution possible, use:
    ```
    function(resolution=Resolution.MAX)
    ```
    When you want an image that's 300 pixels wide, use:
    ```
    function(resolution=Resolution.fixed_size(width=300))
    ```
    """

    MAX = "max"  # Maximum resolution possible

    @staticmethod
    def fixed_size(width: int = AUTO, height: int = AUTO, allow_upscaling=False) -> str:
        """Used for getting the image at a fixed width or height (or both).

        The string that is generated is according to the IIIF image API.
        https://iiif.io/api/image/3.0/
        """
        if type(width) != int or type(height) != int:
            raise TypeError("Arguments should be integers.")
        if not height and not width:
            raise ValueError("No width or height given, give at least one.")

        form = ","
        if width:
            form = str(width) + form
        if height:
            form = form + str(height)

        if allow_upscaling:
            form = "^" + form

        return form

    @staticmethod
    def percentage_size(size_percentage: int) -> str:
        """Used for getting the image at a fixed percentage size.

        The string that is generated is according to the IIIF image API.
        https://iiif.io/api/image/3.0/
        """
        if type(size_percentage) != int:
            raise TypeError("Arguments should be integers.")

        if size_percentage <= 100:
            return f"pct:{size_percentage}"
        else:
            # ^ needed for upscaling above 100%
            return f"^pct:{size_percentage}"


class MapSheet:
    """Main class of the project, containing the information of a IIIF map sheet.

    It's used to manage it's data, including
    - loading the mapsheet from a json annotation file
    - writing it to a json annotaiton file
    - Setting the mask and georeference.
    - Plotting the mapsheet
    - Getting the image (since it's online and not stored in the class)
    """

    id: str
    _image_endpoint: str
    _mask: "Mask"
    _georeference: Union["Georeference", None]
    metadata: dict[str, Any]

    def __init__(self, image_endpoint: str) -> None:
        self.id = "Untitled MapSheet"
        self._image_endpoint = image_endpoint
        self.metadata = {}
        self._georeference = None
        self._mask = RectangleMask.full_image(image_endpoint)

    @classmethod
    def from_annotation(cls, annotation: dict[str, Any]) -> "MapSheet":
        """Load the IIIF mapsheet data from its json annotation file"""
        endpoint = annotation["target"]["service"][0]["@id"]
        self = cls(endpoint)
        self.id = annotation["id"]
        self._mask = Mask.from_svg_selector(annotation["target"]["selector"])
        if not annotation["body"]:
            self._georeference = None
        else:
            self._georeference = Georeference.from_geojson_dict(annotation["body"])

        self.metadata = annotation.get("metadata", {})
        return self

    @classmethod
    def from_annotationpage(cls, annotationpage: str) -> "MapSheet":
        data = json.loads(annotationpage)
        return cls.from_annotation(data["items"][0])

    def to_annotation(self) -> dict[str, Any]:
        """Write the IIIf mapsheet."""
        annotation = {}
        annotation["id"] = self.id
        annotation["@context"] = [
            "http://www.w3.org/ns/anno.jsonld",
            "http://geojson.org/geojson-ld/geojson-context.jsonld",
            "http://iiif.io/api/presentation/3/context.json"
        ]
        annotation["type"] = "Annotation"
        annotation["motivation"] = "georeferencing"

        annotation["target"] = {"type": "Image"}
        annotation["target"]["source"] = self._image_endpoint + "/full/full/0/default.jpg"
        annotation["target"]["selector"] = self._mask.as_svg_selector()
        annotation["target"]["service"] = [{
            "@id": self._image_endpoint,
            "type": "ImageService2"
        }]

        if self._georeference:
            annotation["body"] = self._georeference.as_geojson_dict()
        else:
            annotation["body"] = {}

        annotation["metadata"] = self.metadata

        return annotation

    def to_annotationpage(self, indent=4) -> str:
        annotationpage = {
            "type": "AnnotationPage",
            "@context": [
                "http://www.w3.org/ns/anno.jsonld"
            ],
            "items": [self.to_annotation()]
        }

        return json.dumps(annotationpage, indent=indent)

    def plot(self) -> None:
        img = self.get_image(Resolution.percentage_size(50))
        plt.figure(dpi=300)
        plt.title(f"{self.id}: {self.metadata['title']}")
        plt.imshow(img)
        plt.show()

    def set_mask(self, mask: "Mask") -> None:
        self._mask = mask

    def set_georeference(self, georeference: "Georeference") -> None:
        self._georeference = georeference

    def get_image(self, resolution=Resolution.MAX) -> "Cv2Image":
        """Quick way to get the scan image of this mapsheet as opencv image/array.

        Args:
            resolution (Resolution, optional): Use the Resolution class for easier and
            more readable passing of resolutions. Defaults to Resolution.MAX.

        Returns:
            Cv2Image: A numpy array of the image in opencv's default color mode.
        """
        return self._get_image("full", resolution, 0)

    def get_image_region(
        self, x: int, y: int, width: int, height: int, resolution=Resolution.MAX
    ) -> "Cv2Image":
        """The same as get_image, but with a cropped out region.

        Args:
            x (int): Number of horizontal pixels from the top left of the image to the top left of
            the crop region.
            y (int): Number of vertical pixels from the top left of the image to the top left of
            the crop region.
            width (int): Width of the crop region in pixels.
            height (int): Height of the crop region in pixels.
            resolution (Resolution, optional): _description_. Use the Resolution class for easier and
                more readable passing of resolutions. Defaults to Resolution.MAX.

        Returns:
            Cv2Image: A numpy array of the image in opencv's default color mode.
        """
        region = f"{x},{y},{width},{height}"
        return self._get_image(region, resolution, 0)

    def _get_image(
        self, region: str, resolution: str, rotation: Union[int, str]
    ) -> "Cv2Image":
        """Private function to prevent duplicate code."""
        url = f"{self._image_endpoint}/{region}/{resolution}/{rotation}/default.jpg"
        response = requests.get(url)
        if response.status_code == 200:  # OK
            image = Image.open(BytesIO(response.content))
            return np.array(image)
        else:
            raise RuntimeError("Failed to download image from url: {url}")

    @property
    def mask(self):
        return self._mask
