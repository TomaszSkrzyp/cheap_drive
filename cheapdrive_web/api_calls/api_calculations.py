from geopy.distance import geodesic

from geopy.geocoders import Nominatim
from .api_exceptions import CoordsFetchError

def get_coordinates(address: str, param: str = None) -> tuple:
    """
    Retrieves the geographic coordinates (longitude, latitude) for a given address using the Nominatim geocoder.

    Args:
        address (str): The address to geocode.
        param (str, optional): An optional parameter used in error messages.

    Returns:
        tuple: A tuple (longitude, latitude) if the address is found.

    Raises:
        CoordsFetchError: If the coordinates cannot be retrieved.
    """

    geolocator = Nominatim(user_agent="cheapdrive")
    location = geolocator.geocode(address)
    if location:
        # Return in (longitude, latitude) order for compatibility with GIS Points.
        return location.longitude, location.latitude
    else:
        raise CoordsFetchError(param or address)
