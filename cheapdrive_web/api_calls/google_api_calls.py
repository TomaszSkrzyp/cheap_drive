
import googlemaps 
import os
from .api_exceptions import AddressError
import requests

def address_validation_and_distance(origin: str, destination: str) -> tuple:
    """
    Validates the provided origin and destination addresses using the Google Maps Distance Matrix API 
    and retrieves the driving distance (in kilometers) and duration (in minutes), along with corrected addresses.

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
    Retrieves the driving distance (in kilometers) and duration (in minutes) between the given origin and 
    destination using the Google Maps Distance Matrix API.

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
    
    try:
        result = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving")
    except Exception as e:
        raise AddressError(f"Google Maps API request failed: {e}")

    # Validate API response structure
    if "rows" not in result or not result["rows"] or "elements" not in result["rows"][0] or not result["rows"][0]["elements"]:
        raise AddressError("Invalid API response: Missing distance data.")

    element = result["rows"][0]["elements"][0]
    status = element.get("status")

    if status == "OK":
        # Ensure distance and duration fields exist before accessing
        if "distance" not in element or "duration" not in element:
            raise AddressError("Missing distance or duration data in API response.")

        distance_km = element["distance"]["value"] / 1000.0  # Convert meters to kilometers
        duration_min = element["duration"]["value"] / 60.0  # Convert seconds to minutes
        return distance_km, duration_min

    if status == "ZERO_RESULTS":
        raise AddressError("No valid route found between the given addresses.")

    raise AddressError(f"Unable to retrieve distance. API status: {status}")

