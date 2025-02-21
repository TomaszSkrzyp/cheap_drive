from typing import List, Optional, Tuple, Union,Set
import time
import math
from concurrent.futures import ThreadPoolExecutor
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from api_calls.api_calculations import get_coordinates
from entry.models import Station
import logging

logger = logging.getLogger("my_logger")


def calculate_perpendicular_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    lat3: float, lon3: float
) -> float:
    """
    Calculates the perpendicular distance (in kilometers) from a point (lat3, lon3)
    to the line defined by two points (lat1, lon1) and (lat2, lon2).

    The function converts all coordinates to radians, computes the cross product
    of the vectors defined by the line and the vector from the first point to the third,
    and then scales the result by Earth's radius (6371 km).

    Args:
        lat1, lon1: Coordinates of the first point defining the line.
        lat2, lon2: Coordinates of the second point defining the line.
        lat3, lon3: Coordinates of the point to which the perpendicular distance is calculated.

    Returns:
        float: The perpendicular distance in kilometers.
    """
    # Convert all coordinates from degrees to radians.
    lat1, lon1, lat2, lon2, lat3, lon3 = map(math.radians, [lat1, lon1, lat2, lon2, lat3, lon3])
    
    # Compute vector differences.
    dx12 = lon2 - lon1
    dy12 = lat2 - lat1
    dx13 = lon3 - lon1
    dy13 = lat3 - lat1

    # Compute the magnitude of the cross product (area of parallelogram formed).
    cross_product = abs(dx12 * dy13 - dy12 * dx13)
    denominator = math.sqrt(dx12**2 + dy12**2)

    # Return the perpendicular distance (scaled by Earth's radius: 6371 km).
    return (cross_product / denominator) * 6371


def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculates the great-circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1, lon1: Coordinates of the first point.
        lat2, lon2: Coordinates of the second point.

    Returns:
        float: The distance in kilometers.
    """
    # Convert coordinates to radians.
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Compute differences.
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    
    # Apply the Haversine formula.
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def find_gas_within_range(
    origin_point: Tuple[float, float],
    destination_point: Tuple[float, float],
    estimated_range: float,
    full_tank_range: float
) -> Union[List[Tuple[int, any]], List]:
    """
    Finds gas stations within an estimated range from the origin that are also within the 
    full-tank range from the destination.

    The function queries for stations whose location is within the estimated range of the origin.
    Then it filters those stations by checking that the distance from the destination does not
    exceed the full_tank_range. If no stations qualify, it returns a failure signal along with
    all stations found within the estimated range.

    Args:
        origin_point: Tuple containing (latitude, longitude) for the origin.
        destination_point: Tuple containing (latitude, longitude) for the destination.
        estimated_range: Search range in kilometers from the origin.
        full_tank_range: Maximum distance in kilometers the vehicle can travel on a full tank.

    Returns:
        List of station tuples (station_id, station_obj) if criteria are met;
        otherwise, returns a list where the first element is the string "failure" and the second
        is the list of stations found within the estimated range.
    """
    origin_lat, origin_lon = origin_point
    dest_lat, dest_lon = destination_point

    # Build a Point object for the origin.
    origin = Point(origin_lat, origin_lon)
    
    # Query stations within the estimated range (in km) from the origin.
    stations_within_range = list(
        Station.objects.filter(
            location__distance_lte=(origin, D(km=estimated_range))
        ).values_list("id", "location")
    )
    
    # Filter stations by checking if their distance to the destination is within full_tank_range.
    qualified_stations = [
        station for station in stations_within_range
        if calculate_distance(dest_lat, dest_lon, station[1].x, station[1].y) <= full_tank_range
    ]
    
    if not qualified_stations:
        # Return a failure signal along with all stations found if no station qualifies.
        return ["failure", stations_within_range]
    
    return qualified_stations


def find_gas_near_route(
    stations: List[Tuple[int, any]],
    origin: Tuple[float, float],
    destination: Tuple[float, float]
) -> List[Tuple[int, any]]:
    """
    Filters a list of gas stations to those located near the straight-line route between
    the origin and destination.

    A station is considered "near the route" if its perpendicular distance from the straight-line
    path is less than or equal to an acceptable detour radius, defined as the larger of one-quarter
    of the total route distance or 10 kilometers.

    Args:
        stations: List of station tuples (station_id, station_obj).
        origin: Tuple (latitude, longitude) for the route's origin.
        destination: Tuple (latitude, longitude) for the route's destination.

    Returns:
        List of station tuples that are near the route.
    """
    origin_lat, origin_lon = origin
    dest_lat, dest_lon = destination

    # Compute the acceptable detour radius.
    route_distance = calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
    detour_radius_km = max(route_distance / 4, 10)

    near_route = []
    for station in stations:
        # Calculate the perpendicular distance from the station to the route.
        perp_distance = calculate_perpendicular_distance(
            origin_lat, origin_lon, dest_lat, dest_lon,
            station[1].x, station[1].y
        )
        if perp_distance <= detour_radius_km:
            near_route.append(station)
    return near_route


def sort_stations_by_distance(
    dest_lat: float,
    dest_lon: float,
    stations_within_range: List[Tuple[int, any]]
) -> List[Tuple[int, any]]:
    """
    Sorts a list of gas stations in ascending order based on their distance to the destination.

    This function computes the distance from each station to the destination in parallel
    and then sorts the stations accordingly.

    Args:
        dest_lat: Latitude of the destination.
        dest_lon: Longitude of the destination.
        stations_within_range: List of station tuples (station_id, station_obj).

    Returns:
        List of station tuples sorted by increasing distance from the destination.
    """
    if not stations_within_range:
        return []

    # Use a thread pool to calculate distances concurrently.
    with ThreadPoolExecutor() as executor:
        distances = list(executor.map(
            lambda station: calculate_distance(dest_lat, dest_lon, station[1].x, station[1].y),
            stations_within_range
        ))
    # Pair each station with its computed distance.
    stations_with_distance = list(zip(stations_within_range, distances))
    
    # Sort stations based on the computed distance.
    sorted_stations = sorted(stations_with_distance, key=lambda x: x[1])
    
    # Return only the station tuples.
    return [station for station, _ in sorted_stations]

from typing import List, Optional, Tuple, Union, Set
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger("my_logger")

# Assume that these helper functions are already defined:
# - find_gas_within_range(origin, destination, estimated_range, full_tank_range)
# - sort_stations_by_distance(dest_lat, dest_lon, stations_list)
# - find_gas_near_route(stations, origin, destination)
# - calculate_distance(lat1, lon1, lat2, lon2)

def filter_bad_start_stations(
    stations: List[Tuple[int, any]], 
    stations_not_to_start_with: Set[int]
) -> List[Tuple[int, any]]:
    """
    Filters out stations whose ID is in the set stations_not_to_start_with.
    
    Args:
        stations: A list of station tuples (station_id, station_obj).
        stations_not_to_start_with: A set of station IDs that should not be used as the starting station.
        
    Returns:
        A list of station tuples that are not in the exclusion set.
    """
    return [station for station in stations if station[0] not in stations_not_to_start_with]


def find_best_gas_stations(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    estimated_range: float,
    full_tank_range: float,
    stations_not_to_start_with: Set[int],
    successful_routes: Optional[List[List[int]]] = None,
    other_stops: Optional[List[Tuple[int, any]]] = None,
    stations_along: Optional[List[int]] = None,
    top_n: int = 3,
    max_stations: int = 6,
) -> Optional[List[List[int]]]:
    """
    Determines candidate routes (lists of station IDs) along the path from the origin to the destination.
    
    The function first searches for gas stations that are within the estimated range from the origin and
    within the full tank range from the destination. If no station has been selected yet (i.e. stations_along
    is empty), it filters out any station whose ID is in stations_not_to_start_with. This prevents reusing 
    stations that previously failed as a starting station. If no stations meet the criteria (i.e. a failure 
    signal is returned), the function relaxes the search criteria recursively by selecting the closest available
    station and updating the origin accordingly. The recursion stops when either enough candidate routes (up to top_n)
    are found or when the number of accumulated stations reaches max_stations.
    
   
    Args:
        origin: A tuple of latitude and longitude representing the starting point.
        destination: A tuple of latitude and longitude representing the destination point.
        estimated_range: The initial search range (in km) from the origin to start looking for stations.
        full_tank_range: The maximum distance (in km) the vehicle can travel on a full tank.
        stations_not_to_start_with: A set of station IDs that have previously failed or should not be used as starting stations.
        successful_routes: An optional list of previously found successful routes.
        other_stops: Optional additional stops that might be relevant for the journey.
        stations_along: Optional list of station IDs used so far in the current route.
        top_n: The number of top routes to return (default is 5).
        max_stations: The maximum number of stations to consider before stopping the search (default is 100).

    Returns:
        A list of lists, where each inner list contains station IDs representing a successful route. 
        Returns None if no successful routes are found.
    
    Notes:
        The function works by iteratively finding stations within the range and filtering them based on their proximity 
        to the origin, detour distance, and whether they have been previously used or failed. If enough valid routes 
        are not found, the function will relax the criteria and continue the search.
    """
    # Function implementation here

    # Initialize mutable parameters if not provided.
    if successful_routes is None:
        successful_routes = []
    if stations_along is None:
        stations_along = []

    logger.debug("Current origin: %s", origin)
    if not origin or not destination:
        logger.debug("Invalid origin or destination provided.")
        return []

    # Query for gas stations within the estimated range.
    range_results = find_gas_within_range(origin, destination, estimated_range, full_tank_range)
    
    # Failure branch: handle when no stations meet the criteria.
    if range_results and range_results[0] == "failure":
        logger.debug("No stations met the criteria in the current search.")
        if len(stations_along) >= max_stations:
            logger.info("Maximum station count (%s) reached. Aborting search.", max_stations)
            return None
        
        # Sort the stations from the failure branch by their distance to the destination.
        sorted_reachable_stations = sort_stations_by_distance(destination[0], destination[1], range_results[1])
        logger.debug("Sorted reachable stations (failure branch):")
        logger.debug([i[0] for i in sorted_reachable_stations ])
        
        logger.debug(stations_along)
        # If no station has been selected yet, filter out stations that are in the exclusion set.
        first_call = len(stations_along) == 0
        if first_call:
            reachable_stations = filter_bad_start_stations(sorted_reachable_stations, stations_not_to_start_with)
            if not reachable_stations:
                logger.debug("Excluding bad stations made this search unfruitful.")
                return None
        else:
            reachable_stations = sorted_reachable_stations
        
        logger.debug("Reachable stations after filtering: %s")
        logger.debug([i[0] for i in reachable_stations])
        closest_station = reachable_stations[0]
        logger.debug("Closest station (failure branch): %s", closest_station)

        # Save other candidate stations (excluding the closest one) for later use.
        other_stops = [s for s in reachable_stations if s != closest_station]
        stations_along.append(closest_station[0])
        
        # Recurse: update the origin to the coordinates of the closest station and relax search ranges.
        return find_best_gas_stations(
            (closest_station[1].x, closest_station[1].y),
            destination,
            full_tank_range,  # The starting fuel is now full tank, therefore estimated range is full tank range
            full_tank_range,  
            stations_not_to_start_with,
            successful_routes,
            other_stops,
            stations_along,
            top_n,
            max_stations,
        )
    else:
        logger.debug("Range results (success branch): %s")
                     
        logger.debug([i[0] for i in range_results ])
        # If no station has been selected yet, filter out bad starting stations.
        first_call = len(stations_along) == 0
        logger.debug(stations_along)
        if first_call:
            available_stations = filter_bad_start_stations(range_results, stations_not_to_start_with)
            if not available_stations:
                logger.debug("Excluding bad stations made this search unfruitful.")
                return None
        else:
            available_stations = range_results
        logger.debug("Available stations after filtering")
        logger.debug([i[0] for i in available_stations ])
        # Retrieve stations near the straight-line route.
        stations_near_route = find_gas_near_route(available_stations, origin, destination)
    
    # Helper: compute total detour distance if a station is selected.
    def compute_total_distance(station: Tuple[int, any]) -> Tuple[Tuple[int, any], float]:
        d_origin_station = calculate_distance(origin[0], origin[1], station[1].x, station[1].y)
        d_station_destination = calculate_distance(station[1].x, station[1].y, destination[0], destination[1])
        return station, d_origin_station + d_station_destination

    # Compute detour distances for candidate stations in parallel.
    with ThreadPoolExecutor() as executor:
        candidate_results = list(executor.map(compute_total_distance, stations_near_route))
    station_by_distances = sorted(candidate_results, key=lambda x: x[1])
    logger.debug("Number of candidate stations: %d", len(station_by_distances))

    # Append candidate routes (each route is a combination of accumulated stations and the candidate station).
    for candidate, _ in station_by_distances[:top_n]:
        if len(successful_routes) == top_n:
            logger.debug("Desired number (%d) of candidate routes reached.", top_n)
            break
        route_candidate = stations_along + [candidate[0]]
        successful_routes.append(route_candidate)
        logger.debug("Added candidate route: %s", route_candidate)

    # If fewer than top_n candidate routes were found, attempt to relax the search further.
    if 0 < len(successful_routes) < top_n:
        logger.debug("Fewer than top_n candidate routes found; attempting to relax search criteria.")
        if other_stops and len(other_stops) > 0:
            second_closest = other_stops[0]
            logger.debug("Relaxation using second closest station: %s", second_closest)
            stations_along[-1] = second_closest[0]
            return find_best_gas_stations(
                (second_closest[1].x, second_closest[1].y),
                destination,
                full_tank_range,
                full_tank_range,
                stations_not_to_start_with,
                successful_routes,
                other_stops,
                stations_along,
                top_n,
                max_stations,
            )

    # If no candidate stations were found at all, return None.
    if not station_by_distances:
        logger.debug("No stations found along the route after processing candidates.")
        return None

    logger.debug("Stations accumulated so far: %s", stations_along)
    logger.debug("Candidate routes so far: %s", successful_routes)
    return successful_routes if stations_along else [[station[0]] for station, _ in station_by_distances[:top_n]]
