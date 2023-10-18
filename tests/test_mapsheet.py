import numpy as np
import pytest
from src import Resolution, MapSheet
from unittest.mock import patch


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


# Test MapSheet class
def test_init():
    sheet = MapSheet("Title", "Endpoint")
    assert sheet.title == "Title"
    assert sheet._image_endpoint == "Endpoint"


# Mocking request for get_image
@patch("requests.get")
def test_get_image(mock_get, sample_image_bytes):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = sample_image_bytes
    sheet = MapSheet("Title", "Endpoint")
    assert isinstance(sheet.get_image(), np.ndarray)  # Your own assertion here


# Mocking request for get_image
@patch("requests.get")
def test_get_image_region(mock_get, sample_image_bytes):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = sample_image_bytes
    sheet = MapSheet("Title", "Endpoint")
    assert isinstance(
        sheet.get_image_region(0, 0, 100, 100), np.ndarray
    )  # Your own assertion here


# Mocking request for get_image
@patch("requests.get")
def test_get_image_failure(mock_get):
    mock_get.return_value.status_code = 404
    sheet = MapSheet("Title", "Endpoint")
    with pytest.raises(RuntimeError):
        sheet.get_image()
