import pytest
from PIL import Image
import io


@pytest.fixture
def sample_image_bytes():
    image = Image.new('RGB', (50, 50), color='red')  # Create a 50x50 red image
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')  # You can change the format to PNG or other file types
    img_byte_arr.seek(0)
    return img_byte_arr.read()
