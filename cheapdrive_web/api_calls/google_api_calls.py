
import googlemaps 
import os
from .api_exceptions import AddressError
import requests

def address_validation_and_distance(origin: str, destination: str) -> tuple:
    """
    Validate the provided origin and destination addresses using the Google Maps Distance Matrix API and
    return the driving distance (in kilometers) and duration (in minutes), along with the corrected addresses.
    
    Args:
        origin (str): The starting address.
        destination (str): The destination address.
    
    Returns:
        tuple: A tuple (distance_km, duration_min, corrected_origin, corrected_destination).
    
    Raises:
        ValueError: If the GOOGLE_API_KEY environment variable is not set.
        AddressError: If the API returns an error for the addresses.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    
    gmaps = googlemaps.Client(key=api_key)
    result = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving")
    
    # Extract the corrected addresses from the API response.
    corrected_origin = result.get("origin_addresses", [None])[0]
    corrected_destination = result.get("destination_addresses", [None])[0]
    
    element = result["rows"][0]["elements"][0]
    status = element.get("status")
    
    if status == "OK":
        # Convert distance from meters to kilometers and duration from seconds to minutes.
        distance_km = element["distance"]["value"] / 1000.0
        duration_min = element["duration"]["value"] / 60.0
        return distance_km, duration_min, corrected_origin, corrected_destination

    # Check for missing or invalid addresses.
    if not corrected_origin and not corrected_destination:
        raise AddressError("Both origin and destination addresses are invalid.")
    if not corrected_origin:
        raise AddressError("Origin address is invalid.")
    if not corrected_destination:
        raise AddressError("Destination address is invalid.")
    if status == "ZERO_RESULTS":
        raise AddressError("No valid route between the given addresses.")
    
    raise AddressError("Unable to validate addresses.")


def distance_gmaps(origin: str, destination: str) -> tuple:
    """
    Retrieve driving distance (in kilometers) and duration (in minutes) between the given origin and destination
    using the Google Maps Distance Matrix API.
    
    Args:
        origin (str): The starting address.
        destination (str): The destination address.
    
    Returns:
        tuple: A tuple (distance_km, duration_min).
    
    Raises:
        ValueError: If the GOOGLE_API_KEY environment variable is not set.
        AddressError: If no valid route is found between the addresses.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    
    gmaps = googlemaps.Client(key=api_key)
    result = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving")
    element = result["rows"][0]["elements"][0]
    status = element.get("status")
    
    if status == "OK":
        distance_km = element["distance"]["value"] / 1000.0
        duration_min = element["duration"]["value"] / 60.0
        return distance_km, duration_min
    
    if not origin and not destination:
        raise AddressError("One of the addresses is missing.")
    
    if status == "ZERO_RESULTS":
        raise AddressError("No valid route found between the given addresses.")
    
    raise AddressError("Unable to retrieve distance.")


def get_route_distance(origin: str, destination: str) -> tuple:
    """
    Retrieve the route distance (in kilometers) and detailed steps between the given origin and destination using the
    Google Directions API.
    
    Args:
        origin (str): The starting address.
        destination (str): The destination address.
    
    Returns:
        tuple: A tuple (distance_km, steps). If the route is not found, returns (None, None).
    
    Raises:
        ValueError: If the GOOGLE_API_KEY environment variable is not set.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    
    route_url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={origin}&destination={destination}&key={api_key}"
    )
    response = requests.get(route_url)
    
    if response.status_code == 200:
        directions_data = response.json()
        if directions_data.get("status") == "OK":
            leg = directions_data["routes"][0]["legs"][0]  # Extract first leg of the route.
            distance_km = leg["distance"]["value"] / 1000.0  # Convert meters to kilometers.
            steps = leg.get("steps", [])
            return distance_km, steps
    return None, None


