from decimal import Decimal
from cache.cache_utils import get_from_cache, set_cache
from django.shortcuts import get_object_or_404
from geopy.distance import geodesic
import time
from api_calls.api_calculations import get_coordinates
from api_calls.google_api_calls import distance_gmaps
from entry.models import Station
from concurrent.futures import ThreadPoolExecutor
from .calculate_consumption import estimate_fuel_consumption
import logging

from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple,Set

logger = logging.getLogger("my_logger")


def parallel_distance_calculations(
    orig_dest_pairs: List[Tuple[Any, ...]], station_ids: List[int]
) -> List[Any]:
    """
    Computes distances in parallel for a list of origin-destination parameter tuples.

    Args:
        orig_dest_pairs: A list of tuples; each tuple contains parameters for get_ptp_distance.
        station_ids: A list of station IDs corresponding to the route segments.

    Returns:
        List: A list of results from get_ptp_distance for each parameter tuple.
    """
    # Extract the origin from the first tuple and the destination from the last tuple.
    origin = orig_dest_pairs[0][0]
    destination = orig_dest_pairs[-1][1]

    # Build cache keys for each route segment:
    #   - The first key combines the origin and the first station ID.
    #   - Intermediate keys combine consecutive station IDs.
    #   - The last key combines the last station ID with the destination.
    route_keys = (
        [origin + str(station_ids[0])]
        + [str(station_ids[i]) + str(station_ids[i + 1]) for i in range(len(station_ids) - 1)]
        + [str(station_ids[-1]) + destination]
    )

    # Associate each route parameter tuple with its corresponding cache key.
    tasks = [(orig_dest_pairs[i], route_keys[i]) for i in range(len(orig_dest_pairs))]

    # Use a ThreadPoolExecutor to compute distances concurrently.
    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda task: get_ptp_distance(
                task[0][0],  # Origin address (or None if not provided)
                task[0][1],  # Destination address (or None if not provided)
                task[0][2],  # Origin coordinates
                task[0][3],  # Destination coordinates
                task[1]      # Cache key for this route segment
            ),
            tasks,
        )
    return list(results)


def get_ptp_distance(
    origin: Optional[str],
    destination: Optional[str],
    origin_coords: Any,
    destination_coords: Any,
    cache_key: Optional[str],
) -> Any:
    """
    Calculates the point-to-point distance and duration between two points using the Google Maps API.
    It first checks a cache for a previously computed result.

    Args:
        origin: The origin address (or None if coordinates are used).
        destination: The destination address (or None if coordinates are used).
        origin_coords: Coordinates for the origin.
        destination_coords: Coordinates for the destination.
        cache_key: Key used to check for a cached distance/duration result.

    Returns:
        Tuple: (distance, duration) as computed by the Google Maps API.
    """
    # Check if the result is cached.
    cached_result = get_from_cache(cache_key)
    if cached_result:
        logger.debug(f"Cache hit for {cache_key}")
        logger.debug(f"Using cached route: {origin_coords}, {destination_coords}")
        return cached_result["distance"], cached_result["duration"]

    # Cache miss: compute using the Google Maps API.
    logger.debug(f"Cache miss for {cache_key}. Using Google Maps API for distance calculation.")
    result = distance_gmaps(origin or origin_coords, destination or destination_coords)

    # Cache the computed result for 2 hours.
    result_json = {"distance": result[0], "duration": result[1]}
    set_cache(cache_key, result_json, timeout=2 * 3600)
    return result


def compute_route_params(
    origin: str,
    station_ids: List[int],
    destination: str,
    origin_coords: Any,
    destination_coords: Any,
) -> List[Tuple[float, float]]:
    """
    Computes route parameters (distances and durations) for a sequence of segments:
    origin -> station(s) -> destination.

    Args:
        origin: The origin address.
        station_ids: A list of station IDs representing gas stations along the route.
        destination: The destination address.
        origin_coords: Coordinates for the origin.
        destination_coords: Coordinates for the destination.

    Returns:
        List of tuples, where each tuple contains (distance, duration) for each segment.
    """
    # Retrieve station coordinates based on the provided station IDs.
    station_coords = [
        (
            get_object_or_404(Station, id=station_id).location.y,
            get_object_or_404(Station, id=station_id).location.x,
        )
        for station_id in station_ids
    ]

    # Build route pairs:
    #   - First segment: origin to first station.
    #   - Intermediate segments: station-to-station.
    #   - Last segment: last station to destination.
    route_pairs: List[Tuple[Any, ...]] = []
    route_pairs.append((origin, None, origin_coords, station_coords[0]))
    if station_coords:
        route_pairs.extend(
            [
                (None, None, station_coords[i], station_coords[i + 1])
                for i in range(len(station_coords) - 1)
            ]
        )
        route_pairs.append((None, destination, station_coords[-1], destination_coords))
    else:
        # If no stations are provided, the route is a single segment.
        route_pairs.append((origin, destination, origin_coords, destination_coords))

    # Compute the route parameters in parallel.
    route_params = parallel_distance_calculations(route_pairs, station_ids)
    return route_params


def determine_best_route(
    origin_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    origin: str,
    destination: str,
    routes: List[List[int]],
    optimal_fuel_consumption: float,
    tank_size: float,
    starting_fuel: float,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[float]]:
    """
    Determines the best route based on duration and fuel efficiency.

    For each candidate route, this function validates segments using a full validation routine.
    It caches validation results for common segments across candidate routes to avoid redundant computations.
    This function also keeps track of stations that should not be chosen as first station as they previously failed
    as starting station of a route(could not be reached from origin)

    Args:
        origin_coords: Coordinates of the origin.
        destination_coords: Coordinates of the destination.
        origin: The origin address.
        destination: The destination address.
        routes: A list of candidate routes (each route is a list of station IDs).
        optimal_fuel_consumption: The vehicle's optimal fuel consumption (liters/100km).
        tank_size: The vehicle's fuel tank capacity.
        starting_fuel: The fuel available at the start of the trip.
        max_stations: Maximum number of stations allowed in a route (default is 6).

    Returns:
        Tuple:
          - best_route_by_time: A dict with route parameters for the fastest route.
          - best_route_by_efficiency: A dict with route parameters for the most fuel-efficient route.
          - efficiency_improvement: The percentage improvement in fuel consumption.
          - failed_first_stations: A set of station IDs that have previously failed as starting stations and
            should not be used as the first station in a route.
        If no valid routes are found, returns None values.
    """
    best_route_duration: Optional[Dict[str, Any]] = None
    best_route_efficiency: Optional[Dict[str, Any]] = None
    best_duration = float("inf")
    best_efficiency = float("inf")
    results: List[Dict[str, Any]] = []

    # Dictionary to store validation results for common segments.
    failed_last_node: Dict[str, bool] = {}
    failed_first_stations: Set[str] = set()

    # Evaluate each candidate route.
    for route_index, route in enumerate(routes):
        start_time = time.time()
        logger.debug(f"Evaluating route {route_index}: {route}")

        route_checked_up_to = 0
        route_passed_validation = True

        # Check cached validation results for common segments.
        for node_index, node in enumerate(route):
            node_key = "_".join([str(i) for i in route[: node_index + 1]])
            validation_result = failed_last_node.get(node_key)
            logger.debug(f"Validation key for segment {node_index}: {node_key}")
            if validation_result is not None:
                if validation_result:
                    logger.debug(
                        f"Skipping route due to failed validation on common segment {node_key}"
                    )
                    route_passed_validation = False
                    break
                else:
                    logger.debug(f"Common segment {node_key} passed validation")
                    route_checked_up_to += 1
        if not route_passed_validation:
            continue

        # Compute route parameters (distances and durations) for each segment.
        route_params = compute_route_params(origin, route, destination, origin_coords, destination_coords)
        if not route_params:
            logger.debug(f"Route {route_index} returned no parameters.")
            continue

        # Separate distances and durations.
        distances, durations = zip(*route_params)
        logger.debug("Route distances: %s", distances)
        logger.debug("Route durations: %s", durations)

        # Validate the segments that have not been previously validated.
        valid, failed_node_index = route_validation(
            
            list(distances)[route_checked_up_to:],
            list(durations)[route_checked_up_to:],
            optimal_fuel_consumption,
            tank_size,
            starting_fuel if route_checked_up_to == 0 else tank_size,
            route_checked_up_to,
        )

        # Record the validation outcome for the segments and return true if the route has failed validation on the first station.
        first_station_fail=save_failed_route(failed_last_node, route, failed_node_index )
        if not valid:
            logger.debug(f"Route {route_index} failed validation at segment {failed_node_index }.")
            if first_station_fail:
                logger.debug("First station fail: "+str(route[0]))
                failed_first_stations.add(route[0])
            
            continue

        # Compute overall metrics for the valid route.
        total_distance = sum(distances)
        total_duration = sum(durations)
        average_speed = total_distance / total_duration if total_duration else 0
        fuel_consumption = float(estimate_fuel_consumption(average_speed)) * total_distance

        # Create a dictionary to store route data.
        route_data = {
            "station_ids": route,
            "distances": distances,
            "durations": durations,
            "fuel_consumption": fuel_consumption,
        }
        results.append(route_data)

        # Update the best (fastest) route.
        if total_duration < best_duration:
            best_duration = total_duration
            best_route_duration = route_data
            logger.debug(f"New best duration route: {route_data['station_ids']} with duration {total_duration}")
        # Update the best (most efficient) route.
        if fuel_consumption < best_efficiency:
            best_efficiency = fuel_consumption
            best_route_efficiency = route_data

        elapsed = time.time() - start_time
        logger.debug(f"Processed route {route_index} in {elapsed:.2f} seconds")

    # Calculate efficiency improvement if more than one valid route exists.
    if len(results) > 1:
        total_other = sum(route["fuel_consumption"] for route in results) - best_efficiency
        avg_other = total_other / (len(results) - 1)
        efficiency_improvement = (1 - best_efficiency / avg_other) * 100
        logger.debug(f"Efficiency improvement: {efficiency_improvement:.2f}%")
    else:
        efficiency_improvement = None
        logger.debug("Not enough routes to calculate efficiency improvement.")

    return best_route_duration, best_route_efficiency, efficiency_improvement,failed_first_stations


def save_failed_route(
    failed_last_node: Dict[str, bool], station_ids: List[int], failed_at: int
) -> None:
    """
    Records validation results for each segment of a route in a dictionary.

    Args:
        failed_last_node: A dictionary to store validation results keyed by segment identifiers.
        station_ids: A list of station IDs representing the route segments.
        failed_at: The index of the segment where validation failed.
    """
    # For each segment, mark whether it passed (False) or failed (True) validation.
    for node_index in range(len(station_ids)):
        node_key = "_".join([str(i) for i in station_ids[: node_index + 1]])
        if node_index < failed_at:
            failed_last_node[node_key] = False
        else:
            failed_last_node[node_key] = True
    if failed_at==0:
        return True


def route_validation(   
    distances: List[float],
    durations: List[float],
    optimal_fuel_consumption: float,
    tank_size: float,
    starting_fuel: float,
    route_checked_up_to: int, 
    safety_coeff: Decimal = Decimal("0.1"),
) -> Tuple[bool, int]:
    """
    Fully validates a candidate route by checking fuel consumption across each segment,
    ensuring that the remaining fuel always exceeds a computed safety margin.

    Args:
        distances: List of distances for each segment.
        durations: List of durations for each segment.
        optimal_fuel_consumption: The optimal fuel consumption (liters/100km).
        tank_size: The vehicle's fuel tank capacity.
        starting_fuel: The fuel available at the start of the route.
        route_checked_up_to: number of segments that were previously validated in that route
        safety_coeff: Coefficient to compute the safety margin (e.g., 0.1).

    Returns:
        Tuple:
          - bool: True if the route is valid; otherwise, False.
          - int: The index of the segment where validation failed (or the number of segments if all pass).
    """
    fuel_left = Decimal(starting_fuel)
    full_tank = Decimal(tank_size)
    consumption_rate = Decimal(optimal_fuel_consumption) / Decimal("100")

    # Compute an initial safety margin for the first segment.
    initial_safety_margin = min(safety_coeff * full_tank / Decimal("2.0"), Decimal(starting_fuel) / Decimal("2"))

    # Evaluate each segment.
    for segment_index, distance in enumerate(distances):
        # Calculate fuel consumption for this segment.
        segment_consumption = consumption_rate * Decimal(distance) * estimate_fuel_consumption(
            (distance / durations[segment_index] * 60)
        )
        if segment_index+route_checked_up_to == 0:
            safety_margin = initial_safety_margin  # Use lower safety margin for the first segment.
        else:
            # Assume a full refuel before subsequent segments.
            fuel_left = full_tank
            safety_margin = safety_coeff * full_tank

        fuel_left -= segment_consumption
        logger.debug(
            f"Segment {segment_index+route_checked_up_to}: distance={distance}, consumption={float(segment_consumption):.2f}, "
            f"fuel_left={float(fuel_left):.2f}, safety_margin={float(safety_margin):.2f}"
        )

        # Fail validation if remaining fuel is below the safety margin.
        if fuel_left < safety_margin:
            logger.debug(
                f"Route fails validation at segment {segment_index+route_checked_up_to}: fuel_left ({float(fuel_left):.2f}) "
                f"is below safety threshold ({float(safety_margin):.2f})."
            )
            return False, segment_index+route_checked_up_to

    # If all segments pass, return True and the total number of segments.
    return True, len(distances)+route_checked_up_to

