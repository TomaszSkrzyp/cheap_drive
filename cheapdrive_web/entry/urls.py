from django.urls import path
from . import views


app_name = 'entry' 

urlpatterns = [
    path("", views.visit, name="visit"),
    path('login/', views.login_view, name='login'),
    
    path('guest/', views.guest_access, name='guest_access'),
    path('register/', views.register, name='register'),
    path('logged/', views.logged_view, name='logged'),
    path('history/', views.trip_history_view, name='trip_history'), 
    
    path('vehicles/', views.user_vehicles_view, name='user_vehicles'),
    path('logout/',views.logout_view,name='logout')
]