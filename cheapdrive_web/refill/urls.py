from django.urls import path
from . import views 

app_name = 'refill' 
urlpatterns = [
     path('results/', views.results, name='results'),
    #for using idspath('load_data/<int:vehicle_id>/<int:trip_id>/', views.load_data, name='load_data'),
    path('load_data/', views.load_data, name='load_data'),
    # ... other URL patterns ...
    path('refill_management/', views.refill_management, name='refill_management'),
    path('choose_option/', views.choose_option, name='choose_option'),
    path('refill_amount/', views.process_fuel_amount, name='refill_amount'),]