from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy

if TYPE_CHECKING:
    from .. import MapSheet
    from ..custom_types import Wgs84Coordinate, Cv2Image

import urllib.parse
import aiohttp
import asyncio
from PIL import Image, ImageOps
from io import BytesIO
import math

total = 0
counter = 0

# Fetches a tile from the server
async def fetch_tile(session, x, y, zoom, iiif_map_link , retries=3):
    url = f"https://allmaps.xyz/{zoom}/{x}/{y}.png?url=" + urllib.parse.quote(iiif_map_link)
    headers = {'User-Agent': 'Mozilla/5.0'}

    for i in range(retries):
        try:
            async with session.get(url, headers=headers, timeout=60) as response:
                global counter
                print(f"Received tile {counter}/{total}")
                counter += 1
                if response.status == 200:
                    content = await response.read()
                    return Image.open(BytesIO(content))
                else:
                    print(f"Failed to get tile {x},{y}. HTTP status code: {response.status}")
                    return None
        except:
            print(f"An error occurred while fetching tile {x},{y}. Retrying...")
            await asyncio.sleep(1)
    print(f"Failed to retrieve tile {x},{y} after {retries} retries.")
    return None

# Constructs a composite image from the tiles
async def construct_composite_image(top_left, bottom_right, zoom, iiif_map_link):
    xtile1, ytile1 = latlon_to_tile(top_left.lat, top_left.lon, zoom)
    xtile2, ytile2 = latlon_to_tile(bottom_right.lat, bottom_right.lon, zoom)

    tile_size = 256
    composite_width = (xtile2 - xtile1 + 1) * tile_size
    composite_height = (ytile2 - ytile1 + 1) * tile_size
    global total
    total = (xtile2 - xtile1 + 1) * (ytile2 - ytile1 + 1)
    composite = Image.new('RGB', (composite_width, composite_height))
    print(f"Requesting {total} tiles.")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for x in range(xtile1, xtile2 + 1):
            for y in range(ytile1, ytile2 + 1):
                task = fetch_tile(session, x, y, zoom, iiif_map_link)
                tasks.append(task)

        images = await asyncio.gather(*tasks)
        print("Done")
        idx = 0
        for x in range(xtile1, xtile2 + 1):
            for y in range(ytile1, ytile2 + 1):
                img = images[idx]
                if img:
                    x_offset = (x - xtile1) * tile_size
                    y_offset = (y - ytile1) * tile_size
                    composite.paste(img, (x_offset, y_offset))
                idx += 1
    composite = cv2.cvtColor(numpy.array(composite), cv2.COLOR_RGB2BGR)
    return composite


def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

@dataclass
class SearchBox:
    top_left: "Wgs84Coordinate"
    bottom_right: "Wgs84Coordinate"

class ReferenceMapResolution:
    LOW = 13
    MEDIUM = 14
    HIGH = 15


class ReferenceMap:
    iiif_map_link: str
    def __init__(self, iiif_map_link: str) -> None:
        self.iiif_map_link = iiif_map_link

    def extract_searchbox(self, searchbox: "SearchBox", resolution: ReferenceMapResolution) -> "Cv2Image":

        # Defines the coordinates of the area of interest
        top_left = searchbox.top_left
        bottom_right = searchbox.bottom_right


        # Creates the composite image
        loop = asyncio.get_event_loop()
        composite = loop.run_until_complete(
            construct_composite_image(
                top_left, bottom_right, resolution, self.iiif_map_link
            )
        )

        return composite