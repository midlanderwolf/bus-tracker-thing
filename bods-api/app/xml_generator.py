from datetime import datetime, timedelta
from typing import List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
from .models import VehicleData, CheckStatusResponse


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 format as required by SIRI"""
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def create_vehicle_activity_xml(vehicle: VehicleData, item_id: str) -> ET.Element:
    """Create VehicleActivity XML element"""

    # Create VehicleActivity element
    vehicle_activity = ET.Element('VehicleActivity')

    # RecordedAtTime
    recorded_time = ET.SubElement(vehicle_activity, 'RecordedAtTime')
    recorded_time.text = format_datetime(vehicle.recorded_at_time)

    # ValidUntilTime
    valid_time = ET.SubElement(vehicle_activity, 'ValidUntilTime')
    valid_time.text = format_datetime(vehicle.valid_until_time)

    # ItemIdentifier (optional)
    if item_id:
        item_id_elem = ET.SubElement(vehicle_activity, 'ItemIdentifier')
        item_id_elem.text = item_id

    # MonitoredVehicleJourney
    mvj = ET.SubElement(vehicle_activity, 'MonitoredVehicleJourney')

    # LineRef
    line_ref = ET.SubElement(mvj, 'LineRef')
    line_ref.text = vehicle.line_ref

    # DirectionRef
    direction_ref = ET.SubElement(mvj, 'DirectionRef')
    direction_ref.text = vehicle.direction_ref

    # PublishedLineName
    published_line_name = ET.SubElement(mvj, 'PublishedLineName')
    published_line_name.text = vehicle.published_line_name

    # OperatorRef
    operator_ref = ET.SubElement(mvj, 'OperatorRef')
    operator_ref.text = vehicle.operator_ref

    # OriginRef
    origin_ref = ET.SubElement(mvj, 'OriginRef')
    origin_ref.text = vehicle.origin_ref

    # OriginName
    origin_name = ET.SubElement(mvj, 'OriginName')
    origin_name.text = vehicle.origin_name

    # DestinationRef
    destination_ref = ET.SubElement(mvj, 'DestinationRef')
    destination_ref.text = vehicle.destination_ref

    # DestinationName (optional)
    if vehicle.destination_name:
        destination_name = ET.SubElement(mvj, 'DestinationName')
        destination_name.text = vehicle.destination_name

    # OriginAimedDepartureTime (optional)
    if vehicle.origin_aimed_departure_time:
        origin_departure = ET.SubElement(mvj, 'OriginAimedDepartureTime')
        origin_departure.text = format_datetime(vehicle.origin_aimed_departure_time)

    # DestinationAimedArrivalTime (optional)
    if vehicle.destination_aimed_arrival_time:
        dest_arrival = ET.SubElement(mvj, 'DestinationAimedArrivalTime')
        dest_arrival.text = format_datetime(vehicle.destination_aimed_arrival_time)

    # VehicleLocation
    vehicle_location = ET.SubElement(mvj, 'VehicleLocation')
    longitude = ET.SubElement(vehicle_location, 'Longitude')
    longitude.text = str(vehicle.longitude)
    latitude = ET.SubElement(vehicle_location, 'Latitude')
    latitude.text = str(vehicle.latitude)

    # Bearing
    bearing = ET.SubElement(mvj, 'Bearing')
    bearing.text = str(vehicle.bearing)

    # Velocity (optional)
    if vehicle.velocity is not None:
        velocity = ET.SubElement(mvj, 'Velocity')
        velocity.text = str(vehicle.velocity)

    # Occupancy (optional)
    if vehicle.occupancy:
        occupancy = ET.SubElement(mvj, 'Occupancy')
        occupancy.text = vehicle.occupancy

    # BlockRef
    block_ref = ET.SubElement(mvj, 'BlockRef')
    block_ref.text = vehicle.block_ref

    # VehicleJourneyRef
    vehicle_journey_ref = ET.SubElement(mvj, 'VehicleJourneyRef')
    vehicle_journey_ref.text = vehicle.vehicle_journey_ref

    # VehicleRef
    vehicle_ref = ET.SubElement(mvj, 'VehicleRef')
    vehicle_ref.text = vehicle.vehicle_ref

    return vehicle_activity


def create_siri_vehicle_monitoring_response(vehicles: List[VehicleData], producer_ref: str = "MIDLANDBUS") -> str:
    """Create complete SIRI-VM XML response"""

    # Create root Siri element
    siri = ET.Element('Siri')
    siri.set('version', '2.0')
    siri.set('xmlns', 'http://www.siri.org.uk/siri')
    siri.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    siri.set('xsi:schemaLocation', 'http://www.siri.org.uk/siri http://www.siri.org.uk/schema/2.0/xsd/siri.xsd')

    # ServiceDelivery
    service_delivery = ET.SubElement(siri, 'ServiceDelivery')

    # ResponseTimestamp
    response_timestamp = ET.SubElement(service_delivery, 'ResponseTimestamp')
    response_timestamp.text = format_datetime(datetime.utcnow())

    # ProducerRef
    producer_ref_elem = ET.SubElement(service_delivery, 'ProducerRef')
    producer_ref_elem.text = producer_ref

    # VehicleMonitoringDelivery
    vmd = ET.SubElement(service_delivery, 'VehicleMonitoringDelivery')

    # ResponseTimestamp (duplicate in VMD as per SIRI spec)
    vmd_response_timestamp = ET.SubElement(vmd, 'ResponseTimestamp')
    vmd_response_timestamp.text = format_datetime(datetime.utcnow())

    # ProducerRef (duplicate in VMD)
    vmd_producer_ref = ET.SubElement(vmd, 'ProducerRef')
    vmd_producer_ref.text = producer_ref

    # ValidUntilTime
    valid_until = ET.SubElement(vmd, 'ValidUntilTime')
    valid_until.text = format_datetime(datetime.utcnow() + timedelta(seconds=30))

    # VehicleActivity elements
    for i, vehicle in enumerate(vehicles):
        item_id = f"MIDL_{i+1}_{int(datetime.utcnow().timestamp())}"
        vehicle_activity = create_vehicle_activity_xml(vehicle, item_id)
        vmd.append(vehicle_activity)

    # Convert to string with proper formatting
    rough_string = ET.tostring(siri, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_check_status_response(status: bool = True, service_started_time: Optional[datetime] = None) -> str:
    """Create SIRI CheckStatus response XML"""

    if service_started_time is None:
        service_started_time = datetime.utcnow()

    # Create root Siri element
    siri = ET.Element('Siri')
    siri.set('version', '2.0')
    siri.set('xmlns', 'http://www.siri.org.uk/siri')
    siri.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

    # CheckStatusResponse
    check_status = ET.SubElement(siri, 'CheckStatusResponse')

    # Status
    status_elem = ET.SubElement(check_status, 'Status')
    status_elem.text = 'true' if status else 'false'

    # ServiceStartedTime
    service_started = ET.SubElement(check_status, 'ServiceStartedTime')
    service_started.text = format_datetime(service_started_time)

    # DataReady
    data_ready = ET.SubElement(check_status, 'DataReady')
    data_ready.text = 'true'

    # Convert to string
    rough_string = ET.tostring(siri, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")