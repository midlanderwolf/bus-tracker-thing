import requests
from django.conf import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TripAPIService:
    """Service for interacting with gladetimes trip APIs"""

    BASE_URL = "https://gladetimes.midlandbus.uk/api"
    TIMEOUT = 10

    @classmethod
    def get_services(cls, operator: str = "NCTR", mode: str = "bus") -> List[Dict]:
        """Get all services for an operator"""
        try:
            params = {
                'format': 'json',
                'mode': mode,
                'operator': operator
            }

            response = requests.get(f"{cls.BASE_URL}/services/", params=params, timeout=cls.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            return data.get('results', [])

        except requests.RequestException as e:
            logger.error(f"Failed to fetch services: {e}")
            return []

    @classmethod
    def get_trips(cls, service_id: int) -> List[Dict]:
        """Get all trips for a specific service"""
        try:
            params = {
                'format': 'json',
                'service': service_id
            }

            response = requests.get(f"{cls.BASE_URL}/trips/", params=params, timeout=cls.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            return data.get('results', [])

        except requests.RequestException as e:
            logger.error(f"Failed to fetch trips for service {service_id}: {e}")
            return []

    @classmethod
    def get_trip_details(cls, service_id: int, vehicle_journey_code: str) -> Optional[Dict]:
        """Get specific trip details"""
        trips = cls.get_trips(service_id)

        for trip in trips:
            if trip.get('vehicle_journey_code') == vehicle_journey_code:
                return trip

        return None

    @classmethod
    def search_services(cls, query: str, operator: str = "NCTR") -> List[Dict]:
        """Search services by line name or description"""
        services = cls.get_services(operator)

        query_lower = query.lower()
        return [
            service for service in services
            if query_lower in service.get('line_name', '').lower() or
               query_lower in service.get('description', '').lower() or
               query_lower in service.get('slug', '')
        ]