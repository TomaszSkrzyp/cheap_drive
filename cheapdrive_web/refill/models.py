from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.gis.db import models as gis_models

from entry.models import User,StationPrices
from refill.route_choice import estimate_fuel_consumption

from django.db.models import Avg

import logging
logger=logging.getLogger("my_logger")


class VehicleData(models.Model):
    """
    Represents a user's vehicle including details such as fuel type, tank size, fuel consumption,
    and whether the vehicle needs a refill.
    """

    class FuelTypes(models.TextChoices):
        DIESEL = "Diesel", "Diesel"
        PB95 = "PB95", "PB95"
        LPG = "LPG", "LPG"
        PB98 = "PB98", "PB98"
    
    class DrivingConditions(models.TextChoices):
        
        city = "City",
        mixed ="Mixed"
        highway =  "Highway"
    

    tank_size = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="The size of the vehicle's fuel tank in liters."
    )
    fuel_type = models.CharField(
        max_length=6,  # Adjusted max length to match the longest choice.
        choices=FuelTypes.choices,
        help_text="The type of fuel used by the vehicle."
    )
    fuel_consumption_per_100km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Fuel consumption in liters per 100 kilometers."
    )
    need_refill = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether the vehicle needs a refill."
    )
    
    # Optional relationship with the User model.
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicle_data",
        help_text="The owner of the vehicle."
    )
    
    driving_conditions = models.CharField(
        max_length=7,  # Adjusted max length to match the longest choice.
        choices=DrivingConditions.choices,
        null=True,
        blank=True,
        help_text="The typical driving conditions in which the fuel usage is given "
    )

    def get_fuel_price_for_station(self, station) -> Decimal:
        """
        Returns the fuel price (as a Decimal) for this vehicle's fuel type at the given station.
        If the station does not have a price for this fuel type, returns the average price across all stations.
        If no price data is available, returns None.

        Args:
            station: A Station object that includes a StationPrices relation.

        Returns:
            Decimal: The fuel price for the vehicle's fuel type.
        """
        # Map the vehicle's fuel type to the appropriate price field.
        FUEL_TYPE_TO_FIELD = {
            self.FuelTypes.DIESEL: "diesel_price",
            self.FuelTypes.PB95: "pb95_price",
            self.FuelTypes.LPG: "lpg_price",
            self.FuelTypes.PB98: "pb98_price",
        }
        price_field = FUEL_TYPE_TO_FIELD.get(self.fuel_type)
        if not price_field:
            return None  # In case of an unexpected fuel type.

        station_price = getattr(station.station_prices, price_field, None)
        if station_price:
            return station_price

        # Compute the average price for the fuel type across all stations.
        average_price = StationPrices.objects.all().aggregate(avg_price=Avg(price_field))["avg_price"]
        if average_price is not None:
            return round(average_price, 2)
        return None

    def __str__(self) -> str:
        return f"{self.user} - {self.fuel_type}"


class TripNode(models.Model):
    """
    Represents a segment (node) in a trip with geographic data, distance, duration,
    and fuel information. Nodes can be chained via the self-referencing 'next_trip' field.
    """
    origin = gis_models.PointField(
        geography=True,
        blank=True,
        null=True,
        help_text="The starting geographic point for this trip node."
    )
    destination = gis_models.PointField(
        geography=True,
        blank=True,
        null=True,
        help_text="The ending geographic point for this trip node."
    )
    distance = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(0.0)],
        help_text="Distance covered in this trip node (in km)."
    )
    duration = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(0.0)],
        help_text="Duration (in minutes) of this trip node."
    )
    currency = models.CharField(
        max_length=3,
        default="PLN",
        help_text="Currency code for any monetary values in this node."
    )
    bought_gas_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        blank=True,
        null=True,
        help_text="Fuel price per liter at the beginning of this node."
    )
    fuel_refilled = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        blank=True,
        null=True,
        help_text="Amount of fuel added (in liters) at the beginning of this node."
    )
    # Self-referencing foreign key to chain trip nodes.
    next_trip = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_node",
        help_text="The next trip node in the sequence."
    )
    station_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="Id of the station thats the origin"
    )
    def delete(self, *args, **kwargs):
        """
        Before deleting this TripNode, update any reverse-related nodes' next_trip reference
        to avoid broken chains.
        """
        if self.previous_node.exists():
            self.previous_node.update(next_trip=None)
        super().delete(*args, **kwargs)

    def get_average_speed(self) -> float:
        """
        Calculates the average speed (in km/h) for this node using:
            (distance / duration) * 60.
        Returns 0 if duration is zero or the calculation is invalid.
        """
        try:
            return (self.distance / self.duration) * 60
        except (InvalidOperation, ZeroDivisionError):
            return 0

    def __str__(self) -> str:
        return f"TripNode: {self.distance} km in {self.duration} min"


class Trip(models.Model):
    """
    Represents a complete trip composed of multiple TripNodes.
    Contains references to the user (or guest), vehicle, origin/destination addresses,
    and the first TripNode (which cascades to subsequent nodes).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The user who owns this trip."
    )
    guest_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Session identifier for guest users."
    )
    vehicle = models.ForeignKey(
        VehicleData,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="trip",
        help_text="Vehicle used during this trip."
    )
    origin_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="The starting address of the trip."
    )
    destination_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="The ending address of the trip."
    )
    first_trip_node = models.ForeignKey(
        TripNode,
        on_delete=models.CASCADE,
        default=None,
        related_name="trips",
        help_text="The first node of the trip."
    )

    def clean(self):
        """
        Validates that the trip has at least one TripNode.
        """
        if not self.first_trip_node:
            raise ValidationError("A trip must have at least one trip node as its starting point.")

    def main_currency(self) -> str:
        """
        Returns the primary currency used in the trip, based on the first TripNode.
        """
        return self.first_trip_node.currency

    def total_distance(self) -> Decimal:
        """
        Calculates the total distance of the trip by traversing all linked TripNodes.
        """
        distance = Decimal("0")
        current_node = self.first_trip_node
        while current_node:
            distance += current_node.distance
            
            logger.debug(current_node.distance)
            current_node = current_node.next_trip
        return distance

    def total_duration(self) -> Decimal:
        """
        Calculates the total duration (in minutes) of the trip by traversing all linked TripNodes.
        """
        duration = Decimal("0")
        current_node = self.first_trip_node
        while current_node:
            duration += current_node.duration
            current_node = current_node.next_trip
        return duration

    def total_price_bought_and_used(self) -> tuple:
        """
        Calculates the total fuel cost:
          - price_bought: The sum cost of fuel purchased (accounting for refills).
          - price_used: An estimate based on the fuel consumption over the distance.
        Returns:
            tuple: (price_bought, price_used) rounded to 2 decimal places.
        """
        price_used = Decimal("0")
        current_node = self.first_trip_node
        # Start with a correction for the first node's cost.
        price_bought = - (current_node.bought_gas_price * current_node.fuel_refilled)

        while current_node:
            price_bought += current_node.bought_gas_price * current_node.fuel_refilled
            fuel_used = (
                current_node.distance *
                self.vehicle.fuel_consumption_per_100km *
                estimate_fuel_consumption(current_node.get_average_speed())
                / Decimal("100")
            )
            price_used += fuel_used * current_node.bought_gas_price
            current_node = current_node.next_trip

        return round(price_bought, 2), round(price_used, 2)

    def fuel_left(self) -> Decimal:
        """
        Calculates the remaining fuel after the trip by subtracting the estimated fuel used
        (based on total distance, vehicle consumption, and average speed adjustment)
        from the total fuel refilled.
        """
        total_refilled = Decimal("0")
        current_node = self.first_trip_node
        while current_node:
            total_refilled += current_node.fuel_refilled
            current_node = current_node.next_trip

        fuel_used = (
            estimate_fuel_consumption(self.get_average_speed()) *
            self.vehicle.fuel_consumption_per_100km *
            self.total_distance() / Decimal("100")
        )
        logger.debug(self.total_distance())
        logger.debug(self.first_trip_node.id)
        fuel_remaining = total_refilled - fuel_used
        return round(fuel_remaining, 2)

    def last_trip_node(self) -> TripNode:
        """
        Retrieves the last TripNode in the linked sequence.
        """
        current_node = self.first_trip_node
        while current_node.next_trip:
            current_node = current_node.next_trip
        return current_node

    def get_average_speed(self) -> float:
        """
        Calculates the overall average speed (in km/h) for the entire trip based on total distance and duration.
        Returns 0 if the calculation fails.
        """
        try:
            return (self.total_distance() / self.total_duration()) * 60
        except (InvalidOperation, ZeroDivisionError):
            return 0

    def save(self, *args, **kwargs):
        """
        Overrides the save method to perform model validation before saving.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        owner = self.user if self.user else "Guest"
        return f"Trip by {owner}: {self.origin_address} -> {self.destination_address}"