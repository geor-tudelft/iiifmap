import json

import numpy as np
import pytest
from src import Resolution, MapSheet
from unittest.mock import patch

from src.custom_types import PixelCoordinate
from src.mask.baseclass import RectangleMask


# Test Resolution class
def test_fixed_size():
    assert Resolution.fixed_size(width=300) == "300,"
    assert Resolution.fixed_size(height=300) == ",300"
    assert Resolution.fixed_size(width=300, height=300) == "300,300"


def test_fixed_size_type_error():
    with pytest.raises(TypeError):
        Resolution.fixed_size(width="300")


def test_fixed_size_value_error():
    with pytest.raises(ValueError):
        Resolution.fixed_size()


def test_percentage_size():
    assert Resolution.percentage_size(50) == "pct:50"
    assert Resolution.percentage_size(200) == "^pct:200"


def test_percentage_size_type_error():
    with pytest.raises(TypeError):
        Resolution.percentage_size("50")


@patch("requests.get")
def test_init(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = json.dumps({"width": 300, "height": 300})
    sheet = MapSheet("Endpoint")
    assert sheet._image_endpoint == "Endpoint"

def test_mapsheet_from_annotationpage(sample_annotationpage):
    sheet = MapSheet.from_annotationpage(sample_annotationpage)
    assert sheet.id == "7044e91ab1c516f6"
    assert sheet._image_endpoint == "https://images.memorix.nl/nai/iiif/8a35a495-f3b3-d957-6404-fc7c870e998c"
    assert not isinstance(sheet._mask, RectangleMask)
    assert sheet._mask._coordinates[0] == PixelCoordinate(796, 731)

def test_mapsheet_from_tmk_annotationpage(sample_tmk_annotationpage):
    sheet = MapSheet.from_annotationpage(sample_tmk_annotationpage)
    assert sheet.id == "7.1.1"
    assert sheet._image_endpoint == "https://service.archief.nl/iip/4a/f2/6b/5c/5b/ee/4a/a3/b4/11/7f/e4/04/97/1b/36/121aa8e4-6947-4b7b-9877-19af473ffc83.jp2"
    assert isinstance(sheet._mask, RectangleMask)
    assert sheet._mask.bottom_left == PixelCoordinate(0, 0)

@pytest.mark.skip  # TODO, make this pass
def test_mapsheet_to_annotationpage(sample_annotationpage):
    sheet = MapSheet.from_annotationpage(sample_annotationpage)
    assert sheet.to_annotationpage() == sample_annotationpage

# Mocking request for get_image
@patch("requests.get")
def test_get_image(mock_get, sample_image_bytes):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = sample_image_bytes
    sheet = MapSheet("Endpoint")
    assert isinstance(sheet.get_image(), np.ndarray)  # Your own assertion here


# Mocking request for get_image
@patch("requests.get")
def test_get_image_region(mock_get, sample_image_bytes):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = sample_image_bytes
    sheet = MapSheet("Endpoint")
    assert isinstance(
        sheet.get_image_region(0, 0, 100, 100), np.ndarray
    )  # Your own assertion here


# Mocking request for get_image
@patch("requests.get")
def test_get_image_failure(mock_get):
    mock_get.return_value.status_code = 404
    sheet = MapSheet("Endpoint")
    with pytest.raises(RuntimeError):
        sheet.get_image()
