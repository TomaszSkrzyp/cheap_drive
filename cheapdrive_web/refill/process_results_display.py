from django.shortcuts import get_object_or_404
from formatters.string_format import format_address, format_duration
from api_calls.other_api_calls import get_address_from_coords
from typing import Any, Dict, List, Optional, Tuple
from entry.models import Station

def process_route_display(trip: Any) -> Tuple[List[Dict[str, Any]], str]:
    """
    Processes trip data and generates a detailed representation of the trip segments, including origin, destination, 
    distance, duration, and stations along the way. It also constructs a Google Maps URL for the route, which includes 
    waypoints for the stations visited.

    Args:
        trip: The trip object containing details about the route and its TripNodes.
            The `trip` object should have:
            - `first_trip_node`: The first node of the trip (typically the origin).
            - `origin_address`: The starting point address of the trip.
            - `destination_address`: The destination address of the trip.
            - Each `trip_node` should include information like station ID, distance, duration, fuel refilled, etc.

    Returns:
        tuple: A tuple containing:
            - `trip_segments`: A list of dictionaries, each representing a segment of the trip. Each dictionary includes:
                - `origin`: The address or station name where the segment starts.
                - `distance`: The distance covered in that segment (formatted in km).
                - `duration`: The time taken for the segment (formatted as HH:MM:SS).
                - `station`: A boolean indicating if the segment is a station.
                - `refill`: The amount of fuel refilled at the station (formatted in liters).
            - `gmaps_url`: A URL string for Google Maps directions, including waypoints for all stations along the route.

    Notes:
        - The function processes the linked list of `TripNodes`, each representing a segment of the trip.
        - For each station node, it fetches station details like the brand name and address from the `Station` model.
        - The Google Maps URL is constructed by combining the origin, destination, and waypoints, allowing the user to view the entire route with stations as stops.
        - The function will treat the first node as the starting point and all subsequent nodes as stations.
    """
    current_node = trip.first_trip_node
    trip_segments: List[Dict[str, Any]] = []
    index = 0  # To track the node position
    waypoint_coords: List[str] = []  # To store station coordinates for waypoints

    # Traverse the linked list of TripNodes.
    while current_node:
        # For nodes other than the first, treat them as stations.
        is_station = (index != 0)
        station = None
        # If it's a station, add its coordinates for the route's waypoint.
        if is_station:
            waypoint_coords.append(f"{current_node.origin.y},{current_node.origin.x}")
        if is_station:
            station = get_object_or_404(Station, id=current_node.station_id)
            
        # Build the segment dictionary.
        segment = {
            "origin": (
                station.station_prices.brand_name.capitalize() + ", " + station.address
                if is_station
                else trip.origin_address
            ),
            "distance": f"{current_node.distance:.2f} km" if current_node.distance != "N/A" else "N/A",
            "duration": format_duration(current_node.duration) if current_node.duration != "N/A" else "N/A",
            "station": is_station,
            "refill": f"{current_node.fuel_refilled:.2f} L" if current_node.fuel_refilled is not None else "N/A",
        }
        trip_segments.append(segment)

        # Move to the next node.
        current_node = current_node.next_trip
        index += 1

    # Construct coordinates for origin and destination.
    origin = trip.origin_address
    destination = trip.destination_address
    # Join waypoint coordinates with a pipe character.
    waypoints = "|".join(waypoint_coords) if waypoint_coords else ""
    # Build the Google Maps URL.
    gmaps_url = (
        f"https://www.google.com/maps/dir/?api=1&origin={origin}"
        f"&destination={destination}&waypoints={waypoints}&travelmode=driving"
    )

    return trip_segments, gmaps_url
