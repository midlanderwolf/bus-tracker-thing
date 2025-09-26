from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Pydantic models for internal use and data validation

class LocationStructure(BaseModel):
    longitude: float = Field(alias='Longitude')
    latitude: float = Field(alias='Latitude')


class MonitoredCall(BaseModel):
    departure_boarding_activity: Optional[str] = Field(default=None, alias='DepartureBoardingActivity')


class MonitoredVehicleJourney(BaseModel):
    line_ref: str = Field(alias='LineRef')
    direction_ref: str = Field(alias='DirectionRef')
    published_line_name: str = Field(alias='PublishedLineName')
    operator_ref: str = Field(alias='OperatorRef')
    origin_ref: str = Field(alias='OriginRef')
    origin_name: str = Field(alias='OriginName')
    destination_ref: str = Field(alias='DestinationRef')
    destination_name: Optional[str] = Field(default=None, alias='DestinationName')
    origin_aimed_departure_time: Optional[datetime] = Field(default=None, alias='OriginAimedDepartureTime')
    destination_aimed_arrival_time: Optional[datetime] = Field(default=None, alias='DestinationAimedArrivalTime')
    vehicle_location: LocationStructure = Field(alias='VehicleLocation')
    bearing: float = Field(alias='Bearing')
    velocity: Optional[float] = Field(default=None, alias='Velocity')
    occupancy: Optional[str] = Field(default=None, alias='Occupancy')
    block_ref: str = Field(alias='BlockRef')
    vehicle_journey_ref: str = Field(alias='VehicleJourneyRef')
    vehicle_ref: str = Field(alias='VehicleRef')
    monitored_call: Optional[MonitoredCall] = Field(default=None, alias='MonitoredCall')


class VehicleActivity(BaseModel):
    recorded_at_time: datetime = Field(alias='RecordedAtTime')
    valid_until_time: datetime = Field(alias='ValidUntilTime')
    item_identifier: Optional[str] = Field(default=None, alias='ItemIdentifier')
    monitored_vehicle_journey: MonitoredVehicleJourney = Field(alias='MonitoredVehicleJourney')


class VehicleMonitoringDelivery(BaseModel):
    response_timestamp: datetime = Field(alias='ResponseTimestamp')
    producer_ref: str = Field(alias='ProducerRef')
    valid_until_time: datetime = Field(alias='ValidUntilTime')
    vehicle_activity: List[VehicleActivity] = Field(alias='VehicleActivity')


class ServiceDelivery(BaseModel):
    response_timestamp: datetime = Field(alias='ResponseTimestamp')
    producer_ref: str = Field(alias='ProducerRef')
    vehicle_monitoring_delivery: VehicleMonitoringDelivery = Field(alias='VehicleMonitoringDelivery')


class Siri(BaseModel):
    version: str = Field(default='2.0')
    service_delivery: ServiceDelivery = Field(alias='ServiceDelivery')


# Check Status Response Models

class CheckStatusResponse(BaseModel):
    status: bool = Field(alias='Status')
    service_started_time: datetime = Field(alias='ServiceStartedTime')
    data_ready: bool = Field(default=True, alias='DataReady')


class StatusResponse(BaseModel):
    version: str = Field(default='2.0')
    check_status_response: CheckStatusResponse = Field(alias='CheckStatusResponse')


# Pydantic models for internal use

class VehicleData(BaseModel):
    vehicle_ref: str
    line_ref: str
    direction_ref: str
    published_line_name: str
    operator_ref: str
    origin_ref: str
    origin_name: str
    destination_ref: str
    destination_name: Optional[str] = None
    origin_aimed_departure_time: Optional[datetime] = None
    destination_aimed_arrival_time: Optional[datetime] = None
    latitude: float
    longitude: float
    bearing: float
    velocity: Optional[float] = None
    occupancy: Optional[str] = None
    block_ref: str
    vehicle_journey_ref: str
    recorded_at_time: datetime
    valid_until_time: datetime