from datetime import datetime, timedelta
from typing import List
import random
from .models import VehicleData


class VehicleDataGenerator:
    """Generates sample vehicle data for BODS compliance testing"""

    def __init__(self):
        # Sample Midland Bus routes and stops
        self.routes = [
            {
                'line_ref': '1',
                'published_line_name': '1 - Birmingham to Dudley',
                'direction_ref': 'OUTBOUND',
                'operator_ref': 'MIDL',
                'origin_ref': '430003002',
                'origin_name': 'Birmingham Moor Street',
                'destination_ref': '430008001',
                'destination_name': 'Dudley Bus Station',
                'origin_departure': '08:00',
                'destination_arrival': '09:30'
            },
            {
                'line_ref': '45',
                'published_line_name': '45 - Walsall to Birmingham',
                'direction_ref': 'INBOUND',
                'operator_ref': 'MIDL',
                'origin_ref': '430007001',
                'origin_name': 'Walsall Bus Station',
                'destination_ref': '430003002',
                'destination_name': 'Birmingham Moor Street',
                'origin_departure': '07:30',
                'destination_arrival': '09:00'
            },
            {
                'line_ref': '47',
                'published_line_name': '47 - West Bromwich to Birmingham',
                'direction_ref': 'OUTBOUND',
                'operator_ref': 'MIDL',
                'origin_ref': '430009001',
                'origin_name': 'West Bromwich Bus Station',
                'destination_ref': '430003002',
                'destination_name': 'Birmingham Moor Street',
                'origin_departure': '08:15',
                'destination_arrival': '09:45'
            }
        ]

        # Sample vehicle locations (simulating movement along routes)
        self.vehicle_positions = [
            {'lat': 52.4786, 'lon': -1.8945, 'bearing': 45.0},  # Birmingham area
            {'lat': 52.4855, 'lon': -1.9020, 'bearing': 90.0},  # Near New Street
            {'lat': 52.4920, 'lon': -1.9180, 'bearing': 135.0}, # Handsworth
            {'lat': 52.5010, 'lon': -1.9350, 'bearing': 180.0}, # Smethwick
            {'lat': 52.5100, 'lon': -1.9520, 'bearing': 225.0}, # West Bromwich
            {'lat': 52.5180, 'lon': -1.9700, 'bearing': 270.0}, # Dudley area
            {'lat': 52.5250, 'lon': -1.9880, 'bearing': 315.0}, # Walsall area
        ]

        self.vehicles = []
        self._generate_vehicles()

    def _generate_vehicles(self):
        """Generate sample vehicles with varying positions"""
        for i in range(10):  # 10 sample vehicles
            route = random.choice(self.routes)
            position = random.choice(self.vehicle_positions)

            vehicle = {
                'vehicle_ref': f'MIDL_{1000 + i}',
                'block_ref': f'BLOCK_{i % 3 + 1}',
                'route': route,
                'position': position,
                'last_update': datetime.utcnow()
            }
            self.vehicles.append(vehicle)

    def get_vehicle_data(self) -> List[VehicleData]:
        """Generate current vehicle data for all vehicles"""
        vehicles_data = []
        now = datetime.utcnow()

        for vehicle in self.vehicles:
            # Simulate movement by slightly changing position
            position = vehicle['position'].copy()
            position['lat'] += random.uniform(-0.001, 0.001)
            position['lon'] += random.uniform(-0.001, 0.001)
            position['bearing'] = (position['bearing'] + random.uniform(-10, 10)) % 360

            # Update last update time
            vehicle['last_update'] = now
            vehicle['position'] = position

            route = vehicle['route']

            # Create vehicle data object
            vehicle_data = VehicleData(
                vehicle_ref=vehicle['vehicle_ref'],
                line_ref=route['line_ref'],
                direction_ref=route['direction_ref'],
                published_line_name=route['published_line_name'],
                operator_ref=route['operator_ref'],
                origin_ref=route['origin_ref'],
                origin_name=route['origin_name'],
                destination_ref=route['destination_ref'],
                destination_name=route['destination_name'],
                origin_aimed_departure_time=self._parse_time(route['origin_departure']),
                destination_aimed_arrival_time=self._parse_time(route['destination_arrival']),
                latitude=position['lat'],
                longitude=position['lon'],
                bearing=round(position['bearing'], 1),
                velocity=random.uniform(0, 25),  # 0-25 m/s (0-90 km/h)
                occupancy=random.choice(['seatsAvailable', 'standingAvailable', 'full', None]),
                block_ref=vehicle['block_ref'],
                vehicle_journey_ref=f'JOURNEY_{vehicle["vehicle_ref"]}_{now.strftime("%Y%m%d")}',
                recorded_at_time=now,
                valid_until_time=now + timedelta(seconds=30)
            )
            vehicles_data.append(vehicle_data)

        return vehicles_data

    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string into datetime object for today"""
        today = datetime.utcnow().date()
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        return datetime.combine(today, time_obj)


# Global instance for the application
vehicle_generator = VehicleDataGenerator()