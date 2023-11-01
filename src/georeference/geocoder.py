import urllib.parse
import requests
import logging
from typing import Optional
import pycountry
from requests import JSONDecodeError

from src.custom_types import Wgs84Coordinate
#import contextily as ctx
# import matplotlib.pyplot as plt
# import webbrowser


def is_valid_iso_country_code(iso_code: str) -> bool:
    try:
        country = pycountry.countries.get(alpha_2=iso_code)
        return country is not None
    except AttributeError:
        return False

# Filters out the country that the geocoder is looking for the toponym in
def geocode(toponym: str, countries_iso_codes: list[str]) -> Optional[Wgs84Coordinate]:
    """
    Finds real world coordinates in WGS84 for the given toponym.

    Uses the World Historical Gazetteer API.

    Args:
        toponym (): Geographic placename to retrieve coordinates for.
        countries_iso_codes (): A list of ISO country codes. Not case-sensitive.

    Returns:
        Wgs84Coordinate if successfully found one match, in any other case returns None.

    Raises:
        ValueError: If no or invalid country codes are provided.
    """

    # Checks if the list is empty
    if not countries_iso_codes:
        raise ValueError('You are giving an empty list.')

    # Checks if the country code is valid based on the ISO standard
    for iso in countries_iso_codes:
        if not is_valid_iso_country_code(iso):
            raise ValueError('You are giving an invalid ISO code.')

    # Makes the HTTP GET request
    country_codes = ','.join(countries_iso_codes)
    url = f'https://whgazetteer.org/api/index?name={urllib.parse.quote(toponym)}&ccode={country_codes},'

    response = requests.get(url)

    # Checks if the request was unsuccessful
    if not response.status_code == 200:
        logging.error('Geocoding request was not successfully processed by the server. ' +
                      'The returned status code is ' + str(response.status_code))
        return None

    # Converts the response to JSON
    try:
        response_json = response.json()
    except JSONDecodeError as error:
        logging.error(f'JSON decode error from Geocoding response for {toponym}. Possible server error.')
        return None

    # Gets the coordinates of each returned feature/match retrieved from the gazetteer
    features = response_json['features']

    # Checks if any matches were found
    if not features:
        logging.error(f'No matches found for {toponym}.')
        return None

    # Checks what happens in the case of a single match and multiple matches
    if len(features) == 1:
        feature = features[0]
        longitude, latitude = feature['geometry']['coordinates']
        return Wgs84Coordinate(latitude, longitude)
    else:
        logging.error(f'More than one matches found for {toponym}.')
        for feature in features:
            logging.debug(f'Found feature: {feature["properties"]["title"]} '
                          f'with class {feature["properties"]["fclasses"]} '
                          #f'and coordinates {feature["geometry"]["coordinates"]}'
                          )
        return None

    # Creates a matplotlib plot
    # fig, ax = plt.subplots()
    #
    # # Plots point (note the use of longitude first in plotting)
    # ax.scatter(longitude, latitude)
    #
    # # Sets up map limits based on the point
    # ax.set_xlim(longitude - 0.25, longitude + 0.25)
    # ax.set_ylim(latitude - 0.25, latitude + 0.25)
    #
    # # Adds background map
    # ctx.add_basemap(ax, crs="epsg:4326", source=ctx.providers.OpenStreetMap.Mapnik)
    #
    # # Shows plot
    # plt.show()
    #
    # webbrowser.open(f"https://bertspaan.nl/latlong/#16/{latitude}/{longitude}")

