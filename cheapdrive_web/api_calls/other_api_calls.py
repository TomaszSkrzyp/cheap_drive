from multiprocessing import Value
from geopy.geocoders import Nominatim
from api_calls.api_exceptions import AddressError,CoordsFetchError
import os
import openrouteservice
import requests
from bs4 import BeautifulSoup
from .api_calculations import get_coordinates

from django.contrib.gis.geos import Point
from entry.models import Station, StationPrices


def retrieve_stations_overpass(brand_names: list, limit: int = 50000) -> list:
    """
    Retrieve fuel stations from the Overpass API within a specified area and filter them by brand names.
    
    Args:
        brand_names (list): List of fuel station brand names to filter.
        limit (int, optional): The maximum number of results to return. Defaults to 50000.
    
    Returns:
        list: A list of dictionaries containing station latitude, longitude, and brand name.
    
    Raises:
        ValueError: If the Overpass API request is unsuccessful.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    # Overpass QL query to fetch fuel stations within a specified radius.
    query = f"""
    [out:json];
    node
      ["amenity"="fuel"]
      (around:360000,51.5,19.8);
    out {limit};
    """
    response = requests.post(overpass_url, data={"data": query})
    
    if response.status_code != 200:
        raise ValueError("Overpass API request was unsuccessful")
    
    data = response.json()
    stations = []
    for station in data.get("elements", []):
        tags = station.get("tags", {})
        station_brand = tags.get("brand", "").lower()
        # Check if the station's brand matches any of the provided brand names.
        for brand in brand_names:
            if brand.lower() in station_brand:
                station_info = {
                    "lat": station.get("lat"),
                    "lon": station.get("lon"),
                    "brand_name": brand.lower(),
                }
                stations.append(station_info)
                break  # Stop checking once a match is found.
    
    return stations


def scrape_prices(brand_name: str) -> tuple:
    """
    Scrape fuel prices for a given fuel station brand from the autocentrum website.
    
    Args:
        brand_name (str): The brand name used in the website URL.
    
    Returns:
        tuple: A tuple (pb95_price, pb98_price, diesel_price, lpg_price). Prices are returned as strings
               (or None if not found).
    """
    url = f"https://www.autocentrum.pl/stacje-paliw/{brand_name}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Initialize prices as None.
    pb95_price = pb98_price = diesel_price = lpg_price = None
    
    # Iterate over all elements that wrap the fuel price information.
    for fuel in soup.find_all("div", class_="last-prices-wrapper"):
        fuel_logo = fuel.find("div", class_="fuel-logo")
        if not fuel_logo:
            continue
        fuel_type = fuel_logo.get_text(strip=True).lower()
        
        price_elem = fuel.find("div", class_="price-wrapper")
        if not price_elem:
            continue
        price_value = price_elem.get_text(strip=True).split()[0]
        
        # Assign prices based on the identified fuel type.
        if fuel_type == "pb":
            pb95_price = price_value
        elif fuel_type == "pb+":
            pb98_price = price_value
        elif fuel_type in ["on", "on+"]:
            # Prefer the "on" price if available.
            if fuel_type == "on+" and diesel_price is not None:
                continue
            diesel_price = price_value
        elif fuel_type in ["lpg", "lpg+"]:
            # Prefer the "lpg" price if available.
            if fuel_type == "lpg+" and lpg_price is not None:
                continue
            lpg_price = price_value
    
    return pb95_price, pb98_price, diesel_price, lpg_price

def get_address_from_coords(lat: float, lon: float) -> str:
    """
    Retrieve a human-readable address from geographic coordinates using reverse geocoding.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
    
    Returns:
        str: The address if found; otherwise, returns "Address not found".
    """
    geolocator = Nominatim(user_agent="cheapdrive")
    location = geolocator.reverse((lat, lon), language="en")
    return location.address if location else "Address not found"
