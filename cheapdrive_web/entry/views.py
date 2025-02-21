
from turtle import update
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from refill.models import Trip
from .forms import UserRegistrationForm  
from api_calls.other_api_calls import get_address_from_coords
import logging
from refill.calculate_consumption import calculate_form_fuel_consumption

logger = logging.getLogger("my_logger")

def register(request: HttpRequest) -> HttpResponse:
    """
    Handles user registration by displaying the registration form, validating 
    the input data, and saving a new user to the database. After successful 
    registration, the user is redirected to the login page.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The rendered registration form or a redirect to the login page.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Create and save the user
            messages.success(request, 'Registration successful!')
            return redirect('entry:login')
        messages.error(request, 'Invalid registration information.')
    else:
        form = UserRegistrationForm()
    return render(request, 'entry/register.html', {'form': form})

def visit(request: HttpRequest) -> HttpResponse:
    """
    Renders the 'visit' page.

    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The rendered visit page.
    """
    return render(request, 'entry/visit.html')

def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user authentication and login. If the user is authenticated, 
    they are redirected to the logged-in view. If not, an authentication form 
    is displayed, and the credentials are validated. Upon successful login, 
    the user is redirected to the next page.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The rendered login page or a redirect to the logged-in page.
    """
    if request.user.is_authenticated:
        return redirect('entry:logout')  
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username: str = form.cleaned_data['username']
            password: str = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                next_url = request.GET.get('next', 'entry:logged')
                return redirect(next_url)
            messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid form data.')
    else:
        form = AuthenticationForm()
        if 'next' in request.GET:
            messages.error(request, 'You must be logged in to access that page.')
    
    response = render(request, 'entry/login.html', {'form': form})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Logs out the user and redirects them to the visit page with a success message.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: A redirect to the visit page after logging out.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('entry:visit')

def guest_access(request: HttpRequest) -> HttpResponse:
    """
    Grants guest access by setting a session flag and redirects to a guest 
    data loading page.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: A redirect to the guest data page.
    """
    request.session['is_guest'] = True
    return redirect(f"{reverse('refill:load_data')}?vehicle_id=none&trip_id=none")

@login_required(login_url='/login/')
def logged_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user navigation after logging in. Displays options for history, 
    user vehicles, new trip creation, or logging out. Redirects based on user 
    action.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: A redirect to the chosen action or the logged-in view.
    """
    if request.method == 'POST':
        action: str = request.POST.get('action', '')
        action_map = {
            'history': 'entry:trip_history',
            'user_vehicles': 'entry:user_vehicles',
            'new_trip': f"{reverse('refill:load_data')}?vehicle_id=none&trip_id=none",
            'logout': 'entry:logout'
        }
        
        if action in action_map:
            return redirect(action_map[action])
        
        messages.error(request, "Invalid action selected.")
    
    return render(request, 'entry/logged.html')

@login_required(login_url='/login/')
def trip_history_view(request: HttpRequest) -> HttpResponse:
    """
    Displays the trip history for the logged-in user. It retrieves trips from 
    the database and renders them with information such as distance, duration, 
    and price.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The rendered trip history page.
    """
    trips = Trip.objects.filter(user=request.user).order_by('-first_trip_node_id')
    
    trip_data = [
        {
            'origin_address': trip.origin_address,
            'destination_address': trip.destination_address,
            'total_distance': trip.total_distance(),
            'total_duration': trip.total_duration(),
            'total_price': trip.total_price_bought_and_used()[1],
            'currency': trip.main_currency(),
            'trip_id': trip.id,
        }
        for trip in trips
    ]
    
    return render(request, 'entry/trip_history.html', {'trip_data': trip_data})

@login_required(login_url='/login/')
def user_vehicles_view(request: HttpRequest) -> HttpResponse:
    """
    Displays the vehicles owned by the logged-in user, including information 
    such as tank size, fuel type, and fuel consumption. 
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The rendered user vehicles page.
    """
    vehicles = request.user.vehicle_data.all()
    vehicle_data = [
        {
            'tank_size': vehicle.tank_size,
            'fuel_type': vehicle.fuel_type,
            'form_fuel_consumption': calculate_form_fuel_consumption(vehicle.driving_conditions, vehicle.fuel_consumption_per_100km),
            'driving_conditions': str(vehicle.driving_conditions).capitalize(),
            'id': vehicle.id
        }
        for vehicle in vehicles
    ]
    return render(request, 'entry/user_vehicles.html', {'vehicle_data': vehicle_data})
