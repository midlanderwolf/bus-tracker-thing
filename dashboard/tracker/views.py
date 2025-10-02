import json
import requests
import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
import psycopg2
from psycopg2.extras import RealDictCursor
from .models import User, VehiclePosition, TrackingSession, Route
from .services import TripAPIService


def get_bustimes_connection():
    """Get connection to bustimes.org database for user authentication"""
    db_url = settings.DATABASES['bustimes']
    return psycopg2.connect(
        host=db_url['HOST'],
        port=db_url['PORT'],
        dbname=db_url['NAME'],
        user=db_url['USER'],
        password=db_url['PASSWORD']
    )


def get_bustimes_db_connection():
    """Get connection to bustimes.org database for user authentication"""
    db_url = settings.DATABASES['bustimes']
    return psycopg2.connect(
        host=db_url['HOST'],
        port=db_url['PORT'],
        dbname=db_url['NAME'],
        user=db_url['USER'],
        password=db_url['PASSWORD']
    )


def home(request):
    """Home page with map and vehicle tracking"""
    return render(request, 'tracker/home.html')


def login_view(request):
    """Secure login view that ONLY authenticates against bustimes.org database"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, 'tracker/login.html')

        # ONLY check local database for already migrated users
        # NEVER create new accounts automatically
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, "Successfully logged in!")
            return redirect('tracker:dashboard')

        # Check bustimes.org database for authentication
        try:
            conn = get_bustimes_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, password, trusted, ip_address, score
                    FROM users
                    WHERE email = %s AND trusted = true
                """, (email,))
                bustimes_user = cur.fetchone()

            if bustimes_user:
                # Validate password against bustimes hash
                from django.contrib.auth.hashers import check_password
                if check_password(password, bustimes_user[3]):
                    # Migrate trusted user to local database
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'username': bustimes_user[1] or email.split('@')[0],
                            'bustimes_id': bustimes_user[0],
                            'trusted': bustimes_user[4],
                            'ip_address': bustimes_user[5],
                            'score': bustimes_user[6]
                        }
                    )

                    if created:
                        # Set password for new local account
                        user.set_password(password)
                        user.save()
                        messages.success(request, "Account migrated successfully! Welcome!")
                    else:
                        messages.success(request, "Successfully logged in!")

                    # Authenticate and login
                    user = authenticate(request, username=email, password=password)
                    if user:
                        login(request, user)
                        return redirect('tracker:dashboard')
                else:
                    messages.error(request, "Invalid email or password.")
            else:
                messages.error(request, "Account not found or not authorized for tracking.")

        except Exception as e:
            # Log the error but don't create accounts
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bustimes database connection failed: {e}")
            messages.error(request, "Authentication service temporarily unavailable. Please try again later.")

    return render(request, 'tracker/login.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard for tracking"""
    # Get user's active tracking session
    active_session = TrackingSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    # Get available vehicles for dropdown
    from .models import Vehicle
    available_vehicles = Vehicle.objects.filter(is_active=True).order_by('vehicle_unique_ref')

    # Check if active vehicle is custom (not in predefined list)
    is_custom_vehicle = False
    if active_session:
        vehicle_refs = available_vehicles.values_list('vehicle_unique_ref', flat=True)
        is_custom_vehicle = active_session.vehicle_ref not in vehicle_refs

    context = {
        'active_session': active_session,
        'available_vehicles': available_vehicles,
        'is_custom_vehicle': is_custom_vehicle,
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
@require_POST
@csrf_exempt
def start_tracking(request):
    """Start a tracking session with comprehensive journey configuration"""
    try:
        data = json.loads(request.body)
        vehicle_ref = data.get('vehicle_ref')
        line_ref = data.get('line_ref', 'UNKNOWN')

        if not vehicle_ref:
            return JsonResponse({'error': 'Vehicle reference required'}, status=400)

        if not line_ref:
            return JsonResponse({'error': 'Line reference required'}, status=400)

        # End any existing active sessions
        TrackingSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False, end_time=timezone.now())

        # Create new tracking session with journey metadata
        session = TrackingSession.objects.create(
            user=request.user,
            vehicle_ref=vehicle_ref,
            # Store journey configuration in session for later use
            # Note: We might need to extend the model to store this metadata
        )

        # Store journey configuration in session for position updates
        request.session['journey_config'] = {
            'line_ref': line_ref,
            'direction_ref': data.get('direction_ref', 'outbound'),
            'operator_ref': data.get('operator_ref', 'UNKNOWN'),
            'block_ref': data.get('block_ref', ''),
            'vehicle_journey_ref': data.get('vehicle_journey_ref', f'journey_{vehicle_ref}'),
            'origin_ref': data.get('origin_ref', ''),
            'origin_name': data.get('origin_name', ''),
            'destination_ref': data.get('destination_ref', ''),
            'destination_name': data.get('destination_name', ''),
            'occupancy': data.get('occupancy')
        }

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'message': f'Started tracking vehicle {vehicle_ref} on line {line_ref}'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@csrf_exempt
def update_position(request):
    """Update vehicle position from user's device"""
    try:
        data = json.loads(request.body)

        # Get active tracking session
        session = TrackingSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not session:
            return JsonResponse({'error': 'No active tracking session'}, status=400)

        # Get journey configuration from session
        journey_config = request.session.get('journey_config', {})

        # Create vehicle position record with session journey data
        position = VehiclePosition.objects.create(
            vehicle_ref=session.vehicle_ref,
            line_ref=journey_config.get('line_ref', data.get('line_ref', 'UNKNOWN')),
            direction_ref=journey_config.get('direction_ref', data.get('direction_ref', 'outbound')),
            published_line_name=journey_config.get('line_ref', data.get('published_line_name', 'Unknown Route')),
            operator_ref=journey_config.get('operator_ref', data.get('operator_ref', 'UNKNOWN')),
            origin_ref=journey_config.get('origin_ref', data.get('origin_ref', 'UNKNOWN')),
            origin_name=journey_config.get('origin_name', data.get('origin_name', 'Unknown')),
            destination_ref=journey_config.get('destination_ref', data.get('destination_ref', 'UNKNOWN')),
            destination_name=journey_config.get('destination_name', data.get('destination_name')),
            longitude=data['longitude'],
            latitude=data['latitude'],
            bearing=data.get('bearing'),  # Allow None/null values
            velocity=data.get('velocity'),
            occupancy=journey_config.get('occupancy', data.get('occupancy')),
            block_ref=journey_config.get('block_ref', data.get('block_ref', 'UNKNOWN')),
            vehicle_journey_ref=journey_config.get('vehicle_journey_ref', data.get('vehicle_journey_ref', f'journey_{session.vehicle_ref}')),
            recorded_at_time=timezone.now(),
            valid_until_time=timezone.now() + timezone.timedelta(minutes=5)
        )

        # Send to API
        api_data = {
            'vehicle_ref': position.vehicle_ref,
            'line_ref': position.line_ref,
            'direction_ref': position.direction_ref,
            'published_line_name': position.published_line_name,
            'operator_ref': position.operator_ref,
            'origin_ref': position.origin_ref,
            'origin_name': position.origin_name,
            'destination_ref': position.destination_ref,
            'destination_name': position.destination_name,
            'longitude': float(position.longitude),
            'latitude': float(position.latitude),
            'bearing': float(position.bearing) if position.bearing is not None else None,
            'velocity': float(position.velocity) if position.velocity else None,
            'occupancy': position.occupancy,
            'block_ref': position.block_ref,
            'vehicle_journey_ref': position.vehicle_journey_ref,
            'recorded_at_time': position.recorded_at_time.isoformat(),
            'valid_until_time': position.valid_until_time.isoformat(),
        }

        # Send to API service
        api_response = requests.post(f"{settings.API_BASE_URL}/vehicle-position", json=api_data)

        return JsonResponse({
            'success': True,
            'position_id': position.id,
            'api_status': api_response.status_code
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def stop_tracking(request):
    """Stop the current tracking session"""
    try:
        session = TrackingSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if session:
            session.end_session()
            return JsonResponse({
                'success': True,
                'message': f'Stopped tracking vehicle {session.vehicle_ref}'
            })
        else:
            return JsonResponse({'error': 'No active tracking session'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_vehicles(request):
    """Get current vehicle positions for map display"""
    try:
        # Get recent vehicle positions
        positions = VehiclePosition.objects.filter(
            recorded_at_time__gte=timezone.now() - timezone.timedelta(minutes=10)
        ).order_by('-recorded_at_time')

        vehicles = []
        seen_vehicles = set()

        for pos in positions:
            if pos.vehicle_ref not in seen_vehicles:
                vehicles.append({
                    'vehicle_ref': pos.vehicle_ref,
                    'line_ref': pos.line_ref,
                    'latitude': float(pos.latitude),
                    'longitude': float(pos.longitude),
                    'bearing': float(pos.bearing) if pos.bearing is not None else None,
                    'occupancy': pos.occupancy,
                    'recorded_at_time': pos.recorded_at_time.isoformat(),
                })
                seen_vehicles.add(pos.vehicle_ref)

        return JsonResponse({'vehicles': vehicles})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_services(request):
    """Get available services for trip selection"""
    operator = request.GET.get('operator', 'NCTR')

    try:
        services = TripAPIService.get_services(operator)

        # Format for frontend
        formatted_services = [
            {
                'id': service['id'],
                'line_name': service['line_name'],
                'description': service['description'],
                'slug': service['slug'],
                'display_name': f"{service['line_name']} - {service['description']}"
            }
            for service in services
        ]

        return JsonResponse({
            'success': True,
            'services': formatted_services
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_trips(request):
    """Get trips for a specific service"""
    service_id = request.GET.get('service_id')

    if not service_id:
        return JsonResponse({
            'success': False,
            'error': 'Service ID required'
        }, status=400)

    try:
        service_id = int(service_id)
        trips = TripAPIService.get_trips(service_id)

        # Format for frontend
        formatted_trips = [
            {
                'id': trip['id'],
                'vehicle_journey_code': trip['vehicle_journey_code'],
                'ticket_machine_code': trip['ticket_machine_code'],
                'block': trip['block'],
                'start_time': trip['start'],
                'end_time': trip['end'],
                'display_name': f"Trip {trip['vehicle_journey_code']} ({trip['start']} - {trip['end']})"
            }
            for trip in trips
        ]

        return JsonResponse({
            'success': True,
            'trips': formatted_trips
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid service ID'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def load_trip_data(request):
    """Load complete trip data for journey configuration"""
    service_id = request.GET.get('service_id')
    vehicle_journey_code = request.GET.get('vehicle_journey_code')

    if not service_id or not vehicle_journey_code:
        return JsonResponse({
            'success': False,
            'error': 'Service ID and vehicle journey code required'
        }, status=400)

    try:
        service_id = int(service_id)
        trip = TripAPIService.get_trip_details(service_id, vehicle_journey_code)

        if not trip:
            return JsonResponse({
                'success': False,
                'error': 'Trip not found'
            }, status=404)

        # Extract service information
        service = trip.get('service', {})
        operator = service.get('operator', {})

        # Build journey configuration from trip data
        journey_data = {
            'line_ref': service.get('line_name', ''),
            'published_line_name': service.get('line_name', ''),
            'operator_ref': operator.get('noc', ''),
            'block_ref': trip.get('block', ''),
            'vehicle_journey_ref': trip.get('vehicle_journey_code', ''),

            # These would need to be determined from additional API calls
            # or stored mappings, as the trips API doesn't include stop info
            'direction_ref': 'outbound',  # Default assumption
            'origin_ref': '',  # Would need additional API call
            'origin_name': '',
            'destination_ref': '',
            'destination_name': '',

            # Timetable information
            'origin_departure_time': trip.get('start'),
            'destination_arrival_time': trip.get('end'),

            # Additional metadata
            'ticket_machine_code': trip.get('ticket_machine_code', ''),
            'service_id': service_id,
            'trip_id': trip.get('id')
        }

        return JsonResponse({
            'success': True,
            'journey_data': journey_data
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid service ID'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)