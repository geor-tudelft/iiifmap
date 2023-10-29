import pytest
from PIL import Image
import io
import json

from src import MapSeries


@pytest.fixture
def sample_image_bytes():
    image = Image.new('RGB', (50, 50), color='red')  # Create a 50x50 red image
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')  # You can change the format to PNG or other file types
    img_byte_arr.seek(0)
    return img_byte_arr.read()

@pytest.fixture
def sample_manifest() -> str:
    with open("test_resources/example_manifest.json", "r") as f:
        data = f.read()

    return data

@pytest.fixture
def sample_annotationpage() -> str:
    with open("test_resources/example_annotationpage2.json", "r") as f:
        data = f.read()

    return data

@pytest.fixture
def sample_tmk_annotationpage() -> str:
    with open("../project/resources/tmk_field/7.1.1.json", "r") as f:
        data = f.read()

    return data
@pytest.fixture
def sample_mapseries(sample_manifest) -> MapSeries:
    series = MapSeries.from_manifest(sample_manifest)
    assert len(series.mapsheets) == 10

    return series
