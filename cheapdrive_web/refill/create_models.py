from api_calls.google_api_calls import address_validation_and_distance
from api_calls.api_exceptions import AddressError
from api_calls.api_calculations import get_coordinates
from .calculate_consumption import calculate_real_fuel_consumption
from .models import VehicleData, Trip, TripNode
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point
from django.db import transaction
import logging
from decimal import Decimal
logger = logging.getLogger("my_logger")

def create_node(origin, destination, distance: Decimal, duration: Decimal, currency: str,
                price: Decimal, fuel_refilled: Decimal, station_id: int =None):
    """
    Create and return a new TripNode instance with the provided parameters.
    
    Args:
        origin (Point): The starting geographic point.
        destination (Point): The destination geographic point.
        distance (Decimal): The distance covered in this node.
        duration (Decimal): The duration (in minutes) of this node.
        currency (str): Currency code for the monetary values.
        price (Decimal): The fuel price per liter at the beginning of this node.
        fuel_refilled (Decimal): The amount of fuel added at the beginning of this node.
    
    Returns:
        TripNode: The newly created TripNode instance.
    """
    new_node = TripNode.objects.create(
        origin=origin,
        destination=destination,
        distance=distance,
        currency=currency,
        duration=duration,
        fuel_refilled=fuel_refilled,
        bought_gas_price=price,
        station_id=station_id
    )
    return new_node


def create_trip(origin: str, destination: str, currency: str, user, guest_id: str,
                vehicle_id: int, cur_fuel: Decimal, price_of_fuel: Decimal) -> int:
    """
    Create a new Trip along with its first TripNode after validating addresses and calculating
    trip details (distance, duration) using external APIs.
    
    The process includes:
      - Validating and correcting the input addresses using the Google API.
      - Calculating the trip's distance and duration.
      - Converting addresses to geographic points.
      - Wrapping database operations in an atomic transaction.
    
    Args:
        origin (str): The original starting address.
        destination (str): The original destination address.
        currency (str): Currency code for the trip.
        user (User): The user associated with the trip.
        guest_id (str): Guest session identifier (if applicable).
        vehicle_id (int): The primary key for the associated VehicleData.
        cur_fuel (Decimal): The current fuel level for the trip node.
        price_of_fuel (Decimal): The fuel price per liter.
    
    Returns:
        int: The ID of the created Trip.
    
    Raises:
        AddressError: If address validation fails.
        ValidationError: If model validation fails.
        ValueError: If trip details cannot be determined.
    """
    try:
        # Validate addresses and retrieve trip details.
        trip_distance, trip_duration, corrected_origin, corrected_destination = address_validation_and_distance(origin, destination)
        if trip_distance is None or trip_duration is None:
            raise ValueError("Failed to calculate trip details.")
    
        try:
            # Obtain geographic coordinates and create GIS Points.
            origin_coords = get_coordinates(origin)
            destination_coords = get_coordinates(destination)
            origin_location = Point(*origin_coords)         # (longitude, latitude)
            destination_location = Point(*destination_coords) # (longitude, latitude)
        except Exception as e:
            logger.debug(f"Error fetching coordinates: {e}")
            return None
    
        # Use an atomic transaction to ensure database consistency.
        with transaction.atomic():
            first_node = TripNode.objects.create(
                origin=origin_location,
                destination=destination_location,
                distance=trip_distance,
                currency=currency,
                duration=trip_duration,
                fuel_refilled=cur_fuel,
                bought_gas_price=price_of_fuel,
            )
    
            # Lock the vehicle row for update.
            vehicle = VehicleData.objects.select_for_update().get(pk=vehicle_id)
    
            trip = Trip.objects.create(
                origin_address=corrected_origin,
                destination_address=corrected_destination,
                user=user,
                guest_session_id=guest_id,
                first_trip_node=first_node,
                vehicle=vehicle,
            )
    
        return trip.id
    
    except (AddressError, ValidationError) as e:
        raise e


def create_vehicle(tank_size: float, fuel_type: str,driving_conditions: str,form_fuel_consumption: Decimal, ) -> int:
    """
    Create a new VehicleData instance with the given parameters.
    
    Args:
        tank_size (float): The size of the vehicle's fuel tank in liters.
        fuel_type (str): The type of fuel used by the vehicle.
        driving_conditions (str): Typical driving conditions of the car. Used in calculating optimal fuel consumption
        form_fuel_consumption(Decimal): Fuel consumption per 100 km stated in the form by the user
        
    
    Returns:
        int: The ID of the created VehicleData instance, or None if validation fails.
    """
    optimal_fuel_consumption: Decimal = calculate_real_fuel_consumption(
           driving_conditions,
            Decimal(form_fuel_consumption)
        )
    try:
        vehicle = VehicleData.objects.create(
            tank_size=tank_size,
            fuel_type=fuel_type,
            fuel_consumption_per_100km=optimal_fuel_consumption,
            driving_conditions=driving_conditions
        )
        return vehicle.id
    except ValidationError as e:
        logger.debug(f"Validation Error: {e}")
        return None