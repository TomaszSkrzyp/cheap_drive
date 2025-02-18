import re

from typing import  List, Any
def scrape_query_paramaters(request_get: dict) -> tuple:
    """
    Extract the vehicle_id and trip_id parameters from a query dictionary.
    
    Args:
        request_get (dict): Dictionary-like object containing query parameters.
    
    Returns:
        tuple: A tuple (vehicle_id, trip_id). Missing parameters are returned as None.
    
    Raises:
        TypeError: If request_get is not a dictionary.
        KeyError: If 'trip_id' or 'vehicle_id' is missing.
    """
    if not isinstance(request_get, dict):
        raise TypeError("request_get must be a dictionary-like object.")
    
    trip_id_param = request_get.get("trip_id", "none")
    vehicle_id_param = request_get.get("vehicle_id", "none")
    
    if trip_id_param is None or vehicle_id_param is None:
        raise KeyError("Missing 'trip_id' or 'vehicle_id' query parameter.")
    
    vehicle_id = None if vehicle_id_param == "none" else int(vehicle_id_param)
    trip_id = None if trip_id_param == "none" else int(trip_id_param)
    
    return vehicle_id, trip_id

 
        
    
def format_address(address: str) -> str:
    """
    Format an address string by cleaning, splitting, and reassembling its components.
    
    Args:
        address (str): The raw address string.
    
    Returns:
        str: A formatted address string.
    """
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 4:
        return address

    street_number, street_name = parts[1], parts[2]
    country=parts[-1]
    # If street_number is not a valid number, assume it is part of the street name.
    if not re.match(r"^\d+(?:[-/;]\d+)?[A-Za-z]?$", street_number):
        street_name, street_number = street_number, ""
        street_name_index = 2  # Adjust index for city extraction.
    else:
        street_name_index = 3  # City information starts after street info.
    
    # Extract the city name while skipping administrative parts.
    city = ""
    administration = "gmina|voivodeship|county|district|region|okres|metropolis|"
    for i in range(street_name_index, len(parts)):
        if re.search(administration + r"\d{2}-\d{3}" + r"\d{5}", parts[i], re.IGNORECASE):
            if not city:
                city = parts[i]
            break
        city = parts[i]
    
    if street_number:
        return f"{street_name} {street_number}, {city}, {country}"
    else:
        return f"{street_name}, {city}, {country}"

def format_duration(minutes: float) -> str:
    """
    Format a duration given in minutes into a human-readable string.
    
    Args:
        minutes (float): Duration in minutes.
    
    Returns:
        str: A formatted string representing the duration.
    """
    if minutes > 1440:  # More than one day.
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        mins = round(minutes % 60)
        return f"{int(days)} days {int(hours)} hours {mins} minutes"
    elif minutes >= 60:
        hours = round(minutes // 60)
        mins = round(minutes % 60)
        return f"{hours} hours {mins} minutes"
    elif minutes < 1.5:
        return "1 minute"
    else:
        return f"{round(minutes)} minutes"