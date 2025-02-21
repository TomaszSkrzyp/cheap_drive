
from django.shortcuts import get_object_or_404
from decimal import Decimal
from entry.models import Station
from refill.models import Trip,TripNode,VehicleData
from refill.create_models import create_node
import logging

logger = logging.getLogger("my_logger")
def update_trip(trip_id: int, vehicle_id: int, tank_size: float, selected_route: dict) -> int:
    """
    Update an existing trip with new route nodes based on a selected route.

    Args:
        trip_id (int): The ID of the trip to update.
        vehicle_id (int): The ID of the vehicle associated with the trip.
        tank_size (float): The fuel tank size of the vehicle.
        selected_route (dict): Dictionary containing route details such as 'station_ids', 'distances', and 'durations'.
    
    Returns:
        int: The ID of the last TripNode in the updated trip.
    
    Raises:
        ValueError: If required parameters are missing.
        Http404: If the Trip, VehicleData, or Station is not found.
    """

    if not trip_id or not selected_route.get("station_ids") or not vehicle_id:
        raise ValueError("Missing required trip_id, vehicle_id, or station_ids in selected_route.")
    
    trip = get_object_or_404(Trip, id=trip_id)
    vehicle = get_object_or_404(VehicleData, id=vehicle_id)
    
    station_ids = selected_route["station_ids"]
    distances = selected_route["distances"]
    durations = selected_route["durations"]
    
    # Helper function to retrieve a station object by its ID.
    def get_station(station_id: int) -> Station:
        return get_object_or_404(Station, id=station_id)
    
    current_node = trip.first_trip_node
    final_destination = current_node.destination
    logger.debug(final_destination.y)
    # Process the first station: update the first trip node.
    first_station = get_station(station_ids[0])
    current_node.destination = first_station.location
    current_node.distance = Decimal(distances[0])
    current_node.duration = Decimal(durations[0])
    current_node.save()
    
    # Process intermediate stations and link new TripNodes.
    for i in range(1, len(station_ids) + 1):
        station = get_station(station_ids[i - 1])
        # Calculate the amount of fuel needed; if not the last station, use the difference between tank size and fuel left.
        fuel_amount = Decimal(tank_size) - trip.fuel_left() if i < len(station_ids) else Decimal(0)
        # Determine the next destination: next station or the final destination.
        next_destination = get_station(station_ids[i]).location if i < len(station_ids) else final_destination
        
        # Create a new TripNode linking the current destination to the next destination.
        current_node.next_trip= create_node(
            origin=current_node.destination,
            destination=next_destination,
            distance=Decimal(distances[i])  if i < len(station_ids) else Decimal(0),
            duration=Decimal(durations[i]) if i < len(station_ids) else Decimal(0),
            currency=station.station_prices.currency,
            price=vehicle.get_fuel_price_for_station(station),
            fuel_refilled=fuel_amount,
            station_id=station.id
        )
        
        current_node.next_trip.save()
        
        current_node.save()
        current_node = current_node.next_trip
    
    return current_node.id


def finish_updating(fuel_quantity: Decimal, last_node_id: int, last_distance: Decimal, last_duration: Decimal) -> None:
    """
    Finalize the update of a trip node with the provided fuel quantity, distance, and duration.

    Args:
        fuel_quantity (Decimal): The amount of fuel refilled.
        last_node_id (int): The ID of the TripNode to update.
        last_distance (Decimal): The distance for the trip node.
        last_duration (Decimal): The duration for the trip node.
    
    Returns:
        None
    
    Raises:
        Http404: If the TripNode with last_node_id is not found.
    """
    last_node = get_object_or_404(TripNode, id=last_node_id)
    last_node.fuel_refilled = fuel_quantity
    last_node.distance = last_distance
    last_node.duration = last_duration
    last_node.save()
