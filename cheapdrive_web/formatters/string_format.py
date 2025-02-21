import re

def scrape_query_paramaters(request_get: dict) -> tuple:
    """
    Extract the `vehicle_id` and `trip_id` parameters from a query dictionary. 
    Returns `None` for missing or invalid parameters.

    Args:
        request_get (dict): Dictionary-like object containing query parameters.
    
    Returns:
        tuple: A tuple (vehicle_id, trip_id). Missing parameters are returned as None.
    
    Raises:
        TypeError: If `request_get` is not a dictionary.
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
    The address is split into parts, and the components (street name, street number, 
    city, country) are correctly formatted and returned.

    Args:
        address (str): The raw address string to be formatted.
    
    Returns:
        str: A formatted address string, reassembling its components (street, city, country).
    """
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 4:
        return address

    street_number, street_name = parts[1], parts[2]
    country = parts[-1]
    
    # If street_number is not a valid number, assume it's part of the street name.
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
    Convert a duration in minutes into a human-readable string format. The duration 
    is presented in terms of days, hours, and minutes depending on the input.

    Args:
        minutes (float): The total duration in minutes.
    
    Returns:
        str: A formatted string representing the duration in days, hours, and minutes.
    
    Example:
        - For durations longer than 1440 minutes, the function returns days, hours, and minutes.
        - For durations between 60 and 1440 minutes, the result is given in hours and minutes.
        - For durations less than 60 minutes, the function returns the duration in minutes.
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
