from http.client import HTTPSConnection
from api_calls.other_api_calls import scrape_prices,retrieve_stations_overpass,get_address_from_coords
from entry.models import StationPrices,Station
from formatters.string_format import format_address
from django.contrib.gis.geos import Point
import logging
logger=logging.getLogger("my_logger")
def update_brand_prices() -> None:
    """
    Update or create StationPrices objects for a predefined list of fuel station brands by scraping their prices
    from an external website.

    Args:
        None
    
    Returns:
        None

    Raises:
        Exception: If an error occurs while updating the prices for any station brand.
    """
    brands = [
        "circle-k-statoil", "orlen", "shell", "amic", "lotos", "lotos-optima", "bp",
        "moya", "auchan", "tesco", "carrefour", "olkop", "leclerc", "intermarche",
         "huzar", "total"
    ]
    for brand in brands:
        pb95_price, pb98_price, diesel_price, lpg_price = scrape_prices(brand)
        logger.debug('brand')
        # Normalize brand name for database consistency.
        normalized_brand = brand
        if brand == "circle-k-statoil":
            normalized_brand = "circle k"
        elif brand == "lotos-optima":
            normalized_brand = "lotos optima"
        
        # Convert prices from string to float if available; treat "0" or None as missing.
        price_mapping = {
            "pb95_price": None if pb95_price in (0, None) else float(str(pb95_price).replace(",", ".")),
            "pb98_price": None if pb98_price in (0, None) else float(str(pb98_price).replace(",", ".")),
            "diesel_price": None if diesel_price in (0, None) else float(str(diesel_price).replace(",", ".")),
            "lpg_price": None if lpg_price in (0, None) else float(str(lpg_price).replace(",", "."))
        }
        
        try:
            StationPrices.objects.update_or_create(
                brand_name=normalized_brand,
                defaults={
                    "pb95_price": price_mapping["pb95_price"],
                    "pb98_price": price_mapping["pb98_price"],
                    "diesel_price": price_mapping["diesel_price"],
                    "lpg_price": price_mapping["lpg_price"],
                }
            )
        except Exception as e:
            # Log the error (here using print for simplicity).
            print(f"Error updating prices for {normalized_brand}: {e}")


def update_station_objects() -> list:
    """
    Retrieve fuel station data from the Overpass API and update/create corresponding Station objects in the database. 
    Estimated address is taken from an API-based function get_address_from_coords.

    Args:
        None
    
    Returns:
        list: A list of Station objects that were created or updated.

    Raises:
        StationPrices.DoesNotExist: If the station price for a brand is not found.
    """

    brand_names = [
        "circle k", "orlen", "shell", "amic", "lotos", "lotos-optima", "bp", "moya",
        "auchan", "tesco", "carrefour", "olkop", "leclerc", "intermarche",
        "huzar", "total"
    ]
    created_stations = []
    stations_data = retrieve_stations_overpass(brand_names)
    logger.debug(len(stations_data))
    
    for data in stations_data:
        brand = data.get("brand_name")
        lat = data.get("lat")
        lon = data.get("lon")
        # Create a GIS Point (expects parameters as (longitude, latitude)).
        location = Point(lon, lat)
        logger.debug(get_address_from_coords(lat,lon))
        address=format_address(get_address_from_coords(lat,lon))
        logger.debug(address)
       
        try:
            station_prices = StationPrices.objects.get(brand_name=brand)
            station_obj, created = Station.objects.get_or_create(
                location=location,
                station_prices=station_prices,
                address=address
            )
            created_stations.append(station_obj)
        except StationPrices.DoesNotExist:
            logger.debug(f"StationPrices for brand '{brand}' not found. Skipping station.")
    
    return created_stations
