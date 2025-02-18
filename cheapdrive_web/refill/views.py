from decimal import Decimal
import logging
import time
from typing import Tuple, Optional, Any, Dict, List, Set
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from api_calls.api_exceptions import AddressError
from .calculate_consumption import calculate_form_fuel_consumption, calculate_real_fuel_consumption, need_refill, estimate_fuel_consumption

from .route_choice import determine_best_route
from db_updates.refill_model_updates import finish_updating, update_trip
from .models import VehicleData, Trip
from .create_models import create_trip, create_vehicle
from .forms import LoadDataForm
from .gas_station_looker import calculate_distance, find_best_gas_stations
from formatters.string_format import format_duration, scrape_query_paramaters
from entry.models import Station
from .process_results_display import process_route_display


logger = logging.getLogger("my_logger")

def validate_fuel_data(tank_size: float, cur_fuel: float, fuel_input_type: str, cur_fuel_percentage: float) -> None:
    """
    Validates fuel-related data.

    Raises:
        ValidationError: If any of the fuel data is invalid.
    """
    if tank_size <= 0:
        raise ValidationError("Tank size must be positive.")
    if cur_fuel < 0:
        raise ValidationError("Current fuel cannot be negative.")
    if fuel_input_type == 'percentage' and not (0 <= cur_fuel_percentage <= 100):
        raise ValidationError("Fuel percentage must be between 0 and 100.")


@csrf_exempt
def load_data(request: HttpRequest) -> HttpResponse:
    """
    Handles GET and POST requests to load data and create/update a trip and vehicle.

    GET: Renders the load data form with pre-filled initial values if available.
    POST: Validates the form data, creates vehicle and trip records, and redirects to the refill or results view.
    """
    try:
        vehicle_id, trip_id = scrape_query_paramaters(request.GET)
    except (KeyError, TypeError) as e:
        logger.exception("Invalid query parameters:")
        return _handle_error(request, f"Invalid query parameters: {e}")

    trip = Trip.objects.filter(id=trip_id).first() if trip_id else None
    vehicle = VehicleData.objects.filter(id=vehicle_id).first() if vehicle_id else None

    if request.method == 'POST':
        return _handle_post_request(request, trip, vehicle)

    return _render_form(request, trip, vehicle)


def _handle_post_request(request: HttpRequest, trip: Optional[Trip], vehicle: Optional[VehicleData]) -> HttpResponse:
    """
    Processes the POST request from the load_data form.

    Validates the input, creates vehicle and trip objects, and redirects to the appropriate view.
    """
    form: LoadDataForm = LoadDataForm(request.POST)
    if not form.is_valid():
        return _render_form(request, trip, vehicle, form)

    try:
        form_data: Dict[str, Any] = form.cleaned_data
        fuel_input_type: str = 'liters' if form_data['cur_fuel_liters_check'] else 'percentage'
        cur_fuel: float = float(form_data['cur_fuel'])
        validate_fuel_data(float(form_data['tank_size']), cur_fuel, fuel_input_type, form_data['cur_fuel_percentage'])

        user = request.user if request.user.is_authenticated else None
        guest_id = request.session.session_key if not user else None
        vehicle_id = create_vehicle(form_data['tank_size'], form_data['fuel_type'], form_data['driving_conditions'],form_data['fuel_consumption_per_100km'])
        vehicle = VehicleData.objects.get(id=vehicle_id) if vehicle_id else None
        if not vehicle:
            return _handle_error(request, "Vehicle creation failed", form, vehicle, trip)

        trip_id = create_trip(
            form_data['origin_address'],
            form_data['destination_address'],
            form_data['currency'],
            user,
            guest_id,
            vehicle_id,
            cur_fuel,
            form_data['price_of_fuel']
        )
        trip = Trip.objects.get(id=trip_id) if trip_id else None
        if not trip:
            return _handle_error(request, "Trip creation failed", form, vehicle, trip)

        if user:
            vehicle.user = user
            vehicle.save()

        if need_refill(trip.fuel_left(), 0.1, vehicle.tank_size):
            vehicle.need_refill = True
            vehicle.save()
            return redirect(f"{reverse('refill:refill_management')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

        request.session['allowed_to_access_refill_views'] = True
        request.session['distance_coeff'] = 1.2
        return redirect(f"{reverse('refill:results')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    except ValidationError as e:
        logger.exception("Validation Error:")
        return _handle_error(request, f"Validation Error: {e}", form, vehicle, trip)
    except (KeyError, ValueError, AddressError) as e:
        logger.exception("Invalid Input Error:")
        return _handle_error(request, f"Invalid input: {e}. Check the spelling and try again", form, vehicle, trip)
    except Exception as e:
        logger.exception("Unexpected Error:")
        return _handle_error(request, f"An unexpected error occurred: {e}", form, vehicle, trip)


def _render_form(request: HttpRequest, trip: Optional[Trip], vehicle: Optional[VehicleData],
                 form: Optional[LoadDataForm] = None) -> HttpResponse:
    """
    Renders the load data form with initial values pre-filled from existing trip or vehicle data.

    Args:
        request: The HttpRequest object.
        trip: An optional Trip object.
        vehicle: An optional VehicleData object.
        form: An optional pre-initialized LoadDataForm.

    Returns:
        HttpResponse: The rendered load data form.
    """
    initial_data: Dict[str, Any] = {}
    if trip:
        initial_data.update({
            'origin_address': trip.origin_address,
            'destination_address': trip.destination_address,
            'price_of_fuel': trip.first_trip_node.bought_gas_price,
        })
    if vehicle:
        initial_data.update({
            'tank_size': vehicle.tank_size,
            'fuel_type': vehicle.fuel_type,
            'fuel_consumption_per_100km': calculate_form_fuel_consumption(vehicle.driving_conditions,vehicle.fuel_consumption_per_100km),
            'driving_conditions': vehicle.driving_conditions,
        })
    form = form or LoadDataForm(initial=initial_data)
    return render(request, 'refill/load_data.html', {
        'vehicle_id': vehicle.id if vehicle else None,
        'trip_id': trip.id if trip else None,
        'form': form,
    })


def _handle_error(request: HttpRequest, message: str, form: Optional[LoadDataForm] = None,
                  vehicle: Optional[VehicleData] = None, trip: Optional[Trip] = None) -> HttpResponse:
    """
    Helper function that displays an error message and re-renders the load data form.

    Args:
        request: The HttpRequest object.
        message: Error message to display.
        form: Optional LoadDataForm instance.
        vehicle: Optional VehicleData instance.
        trip: Optional Trip instance.

    Returns:
        HttpResponse: The rendered error page (load data form with error message).
    """
    messages.error(request, message)
    return _render_form(request, trip, vehicle, form)


@csrf_exempt
def refill_management(request: HttpRequest) -> HttpResponse:
    """
    Handles the refill management view by extracting parameters, computing route metrics, 
    and determining the optimal gas station route.

    This function extracts query parameters from the request, retrieves the associated
    Trip and VehicleData objects, computes key distances and fuel metrics, and attempts 
    up to three times to find a valid gas station route by adjusting the estimated drive range. 
    Once a valid route is determined based on time and efficiency, it stores the route details 
    in the session and redirects the user to the choose option view. If any step fails, it 
    redirects the user to the load data view with an error message. This function also keeps 
    track of stations that should not be chosen as first station as they previously failed
    as starting station of a route(could not be reached from origin)

    Args:
        request (HttpRequest): The HTTP request containing query parameters for vehicle_id and trip_id.

    Returns:
        HttpResponse: A redirection to either the load data view (in case of an error or invalid data) 
        or the choose option view after successful route determination.
    """
    try:
        vehicle_id, trip_id = scrape_query_paramaters(request.GET)
    except (KeyError, TypeError) as e:
        messages.error(request, f"Invalid query parameters: {e}")
        logger.exception("Error extracting query parameters")
        request.session['allowed_to_access_refill_views'] = False
        return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    # Retrieve the trip and vehicle objects; if either is missing, redirect with an error.
    trip = get_object_or_404(Trip, id=trip_id) if trip_id else None
    vehicle = get_object_or_404(VehicleData, id=vehicle_id) if vehicle_id else None
    if not trip or not vehicle:
        messages.error(request, "Trip or vehicle not found.")
        request.session['allowed_to_access_refill_views'] = False
        return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    # Extract origin and destination coordinates from the first trip node.
    origin_coords: Tuple[float, float] = (trip.first_trip_node.origin.y, trip.first_trip_node.origin.x)
    destination_coords: Tuple[float, float] = (trip.first_trip_node.destination.y, trip.first_trip_node.destination.x)

    # Calculate geographic and road distances.
    geo_distance: float = calculate_distance(
        origin_coords[1], origin_coords[0],
        destination_coords[1], destination_coords[0]
    )
    road_distance: float = float(trip.total_distance())
    # Compute the ratio of the geographic distance to the road distance.
    est_road_to_geo: float = geo_distance / road_distance if road_distance else 1
    logger.debug("Estimated road-to-geographic distance ratio: %s", est_road_to_geo)

    # Compute fuel metrics.
    fuel_at_start: float = float(trip.first_trip_node.fuel_refilled)
    estimated_fuel_consumption: float = float(
        estimate_fuel_consumption(trip.get_average_speed()) * vehicle.fuel_consumption_per_100km
    )

    best_station_routes: Optional[List[List[Any]]] = None
    best_route_by_time: Optional[Dict[str, Any]] = None
    best_route_by_efficiency: Optional[Dict[str, Any]] = None
    improvement: Optional[Any] = None
    stations_not_to_start_with: Set(int)=set()
    # Attempt up to three times to find a valid gas station route by adjusting the estimated drive range.
    for attempt in range(3):
        # The adjustment factor decreases the estimated drive range gradually.
        adjustment_factor: float = (7 / 8) ** (attempt )
        est_drive_range: float = (
            max(fuel_at_start - 0.1 * vehicle.tank_size, 0.05 * vehicle.tank_size) /
            estimated_fuel_consumption *
            est_road_to_geo * 100 * adjustment_factor
        )
        logger.debug(
            "Attempt %d: Looking for a station in range: %.2f with adjustment factor: %.4f",
            attempt + 1, est_drive_range, adjustment_factor
        )

        full_tank_range: float = (
            0.9 * vehicle.tank_size / estimated_fuel_consumption *
            est_road_to_geo * 100 * adjustment_factor
        )

        # Search for the best gas station routes based on the computed ranges.
        best_station_routes = find_best_gas_stations(
            trip.first_trip_node.origin,
            trip.first_trip_node.destination,
            est_drive_range,
            full_tank_range,
            stations_not_to_start_with
         )

        # If no station routes are found and this is the final attempt, return an error.
        if not best_station_routes:
            if attempt == 2:
                messages.error(
                    request,
                    "Invalid data given: The app could not find a reasonable route for this trip"
                )
                logger.debug("Unsuccessful after maximum attempts to find station routes.")
                return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")
            continue

        # Determine the best routes based on travel time and fuel efficiency.
        best_route_by_time, best_route_by_efficiency, improvement, new_invalid_start_stations = determine_best_route(
            origin_coords,
            destination_coords,
            trip.origin_address,
            trip.destination_address,
            best_station_routes,
            vehicle.fuel_consumption_per_100km,
            vehicle.tank_size,
            fuel_at_start
        )
        stations_not_to_start_with.update(new_invalid_start_stations)
        logger.debug("bad start stations:")
        logger.debug(stations_not_to_start_with)
        # If valid routes are found, log success and break out of the loop.
        if best_route_by_time and best_route_by_efficiency:
            logger.info("Stations found on attempt %d", attempt + 1)
            break
        elif attempt == 2:
            logger.info("Invalid data given: The app could not find a reasonable route for this trip")
            messages.error(
                request,
                "Invalid data given: The app could not find a reasonable route for this trip"
            )
            return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")


      # Save the best route details in the session.
    request.session['best_route_by_time'] = best_route_by_time
    request.session['best_route_by_eff'] = best_route_by_efficiency
    request.session['improvement'] = improvement

    # Redirect the user to the choose option view with the required parameters.
    choose_option_url: str = reverse('refill:choose_option')
    return redirect(f"{choose_option_url}?vehicle_id={vehicle_id}&trip_id={trip_id}")


def choose_option(request: HttpRequest) -> HttpResponse:
    """
    Renders a page that allows the user to choose between the best time route and best efficiency route.
    On POST, the chosen route is saved in the session and the user is redirected to the refill amount view.
    
    Returns:
        HttpResponse: The rendered choose option page or a redirect if an error occurs.
    """
    vehicle_id: Optional[str] = request.GET.get('vehicle_id')
    trip_id: Optional[str] = request.GET.get('trip_id')
    best_route_by_time: Optional[Dict[str, Any]] = request.session.get('best_route_by_time')
    best_route_by_eff: Optional[Dict[str, Any]] = request.session.get('best_route_by_eff')
    improvement: Optional[Any] = request.session.get("improvement")

    if not (best_route_by_time and best_route_by_eff):
        messages.error(request, "Route data is missing. Please try again.")
        return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    try:
        routes: Dict[str, Any] = {
            'time': {
                'duration': format_duration(sum(best_route_by_time.get('durations', []))),
                'distance': f"{sum(best_route_by_time.get('distances', [])):.2f} km",
                'data': best_route_by_time
            },
            'eff': {
                'duration': format_duration(sum(best_route_by_eff.get('durations', []))),
                'distance': f"{sum(best_route_by_eff.get('distances', [])):.2f} km",
                'data': best_route_by_eff
            }
        }
    except Exception as e:
        logger.exception(f"Error calculating route totals: {str(e)}")
        messages.error(request, f"Error calculating route totals: {str(e)}")
        return redirect(f"{reverse('refill:choose_option')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    if request.method == 'POST':
        choice: Optional[str] = request.POST.get('choice')
        if choice not in routes:
            messages.error(request, "Invalid choice. Please select a valid option.")
            return redirect(request.path)
        request.session['selected_route'] = routes[choice]['data']
        request.session['trip_status'] = 'not_updated'
        return redirect(f"{reverse('refill:refill_amount')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    return render(request, 'refill/choose_option.html', {
        "routes": routes,
        "improvement": improvement,
    })


def process_fuel_amount(request: HttpRequest) -> HttpResponse:
    """
    Processes fuel refill input from the user.

    GET: Retrieves the selected route and computes the minimum and maximum refill amounts.
    POST: Validates the fuel quantity, updates the trip data, and redirects to the results view.

    Returns:
        HttpResponse: A rendered page for fuel input or a redirection after processing.
    """
    vehicle_id: Optional[str] = request.GET.get('vehicle_id')
    trip_id: Optional[str] = request.GET.get('trip_id')

    if not vehicle_id or not trip_id:
        messages.error(request, "Missing vehicle or trip ID.")
        return redirect(reverse('refill:load_data'))

    if request.method == 'GET' and request.session.get('trip_status') != 'updated':
        selected_route: Optional[Dict[str, Any]] = request.session.get('selected_route')
        if not selected_route:
            messages.error(request, "No selected route found. Redirecting to load data.")
            return redirect(reverse('refill:load_data'))
        vehicle: VehicleData = get_object_or_404(VehicleData, id=vehicle_id)
        trip: Trip = get_object_or_404(Trip, id=trip_id)
        
        try:
            last_distance: float = selected_route['distances'][-1]
            last_duration: float = selected_route['durations'][-1]
            last_station: Station = get_object_or_404(Station, id=selected_route['station_ids'][-1])
            last_station_price: Any = vehicle.get_fuel_price_for_station(last_station)
            last_station_currency: str = last_station.station_prices.currency
            last_station_brand_name: str = last_station.station_prices.brand_name
            last_station_address=last_station.address
            last_node_id: Any = update_trip(trip_id, vehicle_id, vehicle.tank_size, selected_route)
            fuel_left: float = float(trip.fuel_left())
            
            logger.debug(f"Fuel left: {fuel_left}")
            estimated_consumption: float = float(estimate_fuel_consumption((last_distance / last_duration) * 60) * vehicle.fuel_consumption_per_100km)
            #Display 0.00 in case no fuel needs to be added. Typically when the algo is too safe
            min_fuel: float = round(max(last_distance * estimated_consumption / 100 - fuel_left, 0.00),2)
            #Dipslay tank size if more fuel than tank size needs to be added. Will never happen, but just to be safe it's here 
            max_fuel: float = round(min(vehicle.tank_size - fuel_left , vehicle.tank_size),2)
            request.session.update({
                'min_fuel': min_fuel,
                'max_fuel': max_fuel,
                'last_node_id': last_node_id,
                'last_distance': last_distance,
                'trip_status': 'updated',
                'last_duration': last_duration,
                'vehicle_id': vehicle_id,
                'trip_id': trip_id,
                'last_station_price': float(last_station_price),
                'last_station_currency': last_station_currency,
                'last_station_brand_name': last_station_brand_name,
                'last_station_address': last_station.address
            })
        except (IndexError, ValueError) as e:
            messages.error(request, f"Error processing route data: {str(e)}")
            return redirect(reverse('refill:load_data'))
    elif request.method == 'POST' and request.session.get('trip_status') == 'updated':
        
        request.session['trip_status'] = 'not_updated'
        try:
            fuel_quantity: float = float(request.POST.get('fuel_quantity', 0))
            min_fuel: Optional[float] = request.session.get('min_fuel')
            max_fuel: Optional[float] = request.session.get('max_fuel')
            if min_fuel is None or max_fuel is None:
                messages.error(request, "Fuel limits not set. Please retry.")
                return redirect(reverse('refill:load_data'))
            if min_fuel <= fuel_quantity <= max_fuel:
                request.session['allowed_to_access_refill_views'] = True
                logger.debug("Trip updated")
                finish_updating(
                    fuel_quantity,
                    request.session['last_node_id'],
                    request.session['last_distance'],
                    request.session['last_duration']
                )
                return redirect(f"{reverse('refill:results')}?vehicle_id={vehicle_id}&trip_id={trip_id}")
            messages.error(request, "Invalid fuel quantity. Please enter a value within range.")
        except ValueError:
            messages.error(request, "Invalid input. Please enter a valid number.")
    else:
        messages.error(request,"Route is missing. Try again")
        return redirect(f"{reverse('refill:load_data')}?vehicle_id={vehicle_id}&trip_id={trip_id}")

    return render(request, 'refill/fuel_amount.html', {
        'gas_price': request.session.get('last_station_price', "N/A"),
        'currency': request.session.get('last_station_currency', "N/A"),
        
        'address': request.session.get('last_station_address', "N/A"),
       
        'brand_name': request.session.get('last_station_brand_name', "N/A").capitalize(),
        'min_value': request.session.get('min_fuel', 0),
        'max_value': request.session.get('max_fuel', 0),
    })

def results(request: HttpRequest) -> HttpResponse:
    """
    Renders the final results view displaying trip details and statistics.

    This view checks if the user is authorized (via a session flag) to access the results.
    It then extracts vehicle and trip IDs from the query parameters, retrieves the corresponding
    trip and vehicle data, computes cost and trip details (including generating a Google Maps URL),
    and finally renders the results page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered results page.
    """
    # Check if the session allows access to refill views.
    if not request.session.get('allowed_to_access_refill_views', True):
        messages.error(request, "You are not authorized to access this page.")
        return redirect(reverse('refill:load_data'))

    # Reset the session flag to prevent unauthorized re-access.
    request.session['allowed_to_access_refill_views'] = False

    try:
        # Extract vehicle and trip IDs from the query parameters.
        vehicle_id, trip_id = scrape_query_paramaters(request.GET)
    except KeyError as e:
        messages.error(request, f"Invalid query parameters: {e}")
        logger.exception("Invalid query parameters:")
        return redirect(reverse('refill:load_data'))
    except TypeError as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        logger.exception("Unexpected Error:")
        return redirect(reverse('refill:load_data'))

    # Retrieve the Trip and VehicleData objects using the extracted IDs.
    trip: Trip = get_object_or_404(Trip, id=trip_id) if trip_id else None  # type: ignore
    vehicle: VehicleData = get_object_or_404(VehicleData, id=vehicle_id) if vehicle_id else None  # type: ignore

    # Compute cost details for fuel bought and used during the trip.
    cost_bought, cost_used = trip.total_price_bought_and_used()
    logger.debug(f"Total costs: Bought: {cost_bought}, Used: {cost_used}")

    # Process trip segments to obtain display details and a Google Maps URL.
    trip_segments, gmaps_url = process_route_display(trip)

    # Build the context dictionary with all required trip and vehicle details.
    context: Dict[str, Any] = {
        "trip_id": trip_id,
        "vehicle_id": vehicle_id,
        "cost_used": f"{cost_used:.2f} {trip.main_currency()}",
        "duration": format_duration(trip.total_duration()),
        "distance": f"{trip.total_distance():.2f} km",
        "origin": trip.origin_address,
        "destination": trip.destination_address,
        "fuel_left": f"{trip.fuel_left():.2f} litres",
        "needs_refill": vehicle.need_refill,
        "refill_price": f"{cost_bought} {trip.main_currency()}",
        "trip_segments": trip_segments,
        "gmaps_url": gmaps_url,
    }

    # Render the results template with the context data.
    return render(request, "refill/results.html", context)