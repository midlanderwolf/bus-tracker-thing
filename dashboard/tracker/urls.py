from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/start-tracking/', views.start_tracking, name='start_tracking'),
    path('api/update-position/', views.update_position, name='update_position'),
    path('api/stop-tracking/', views.stop_tracking, name='stop_tracking'),
    path('api/vehicles/', views.get_vehicles, name='get_vehicles'),

    # Trip API integration
    path('api/services/', views.get_services, name='get_services'),
    path('api/trips/', views.get_trips, name='get_trips'),
    path('api/load-trip/', views.load_trip_data, name='load_trip_data'),
]