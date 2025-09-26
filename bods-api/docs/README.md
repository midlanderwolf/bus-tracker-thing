# Midland Bus BODS API Documentation

## Overview

This API implements the Bus Open Data Service (BODS) standard using the SIRI-VM (Service Interface for Real-time Information - Vehicle Monitoring) protocol. It provides real-time vehicle location and journey information for Midland Bus services.

## BODS Compliance

This API is fully compliant with the UK Department for Transport's BODS requirements:

- **SIRI-VM 2.0 Standard**: Implements the official CEN SIRI-VM specification
- **Mandatory Elements**: All required fields are populated according to BODS profile
- **Update Frequency**: Data is updated at least every 30 seconds
- **XML Format**: Responses use proper SIRI-VM XML schema
- **Check Status**: Provides operational status endpoint

## API Endpoints

### GET /
Basic API information and available endpoints.

**Response:**
```json
{
  "service": "Midland Bus BODS API",
  "version": "1.0.0",
  "standard": "SIRI-VM 2.0",
  "description": "Real-time vehicle monitoring data for Midland Bus services",
  "endpoints": {
    "check-status": "/check-status",
    "vehicle-monitoring": "/vehicle-monitoring",
    "docs": "/docs"
  }
}
```

### GET /check-status
**BODS Required Endpoint**

Returns the current operational status of the SIRI-VM service.

**Response:** SIRI-VM XML
```xml
<?xml version="1.0" ?>
<Siri version="2.0" xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <CheckStatusResponse>
    <Status>true</Status>
    <ServiceStartedTime>2024-01-15T10:30:00.000Z</ServiceStartedTime>
    <DataReady>true</DataReady>
  </CheckStatusResponse>
</Siri>
```

### GET /vehicle-monitoring
**Main Data Endpoint**

Returns real-time vehicle monitoring data for all active vehicles.

**Query Parameters:**
- `LineRef` (optional): Filter by specific bus line
- `OperatorRef` (optional): Filter by operator code
- `VehicleRef` (optional): Filter by specific vehicle
- `MaximumNumberOfVehicles` (optional): Limit number of results

**Response:** SIRI-VM XML
```xml
<?xml version="1.0" ?>
<Siri version="2.0" xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.siri.org.uk/siri http://www.siri.org.uk/schema/2.0/xsd/siri.xsd">
  <ServiceDelivery>
    <ResponseTimestamp>2024-01-15T10:30:15.000Z</ResponseTimestamp>
    <ProducerRef>MIDLANDBUS</ProducerRef>
    <VehicleMonitoringDelivery>
      <ResponseTimestamp>2024-01-15T10:30:15.000Z</ResponseTimestamp>
      <ProducerRef>MIDLANDBUS</ProducerRef>
      <ValidUntilTime>2024-01-15T10:30:45.000Z</ValidUntilTime>
      <VehicleActivity>
        <RecordedAtTime>2024-01-15T10:30:10.000Z</RecordedAtTime>
        <ValidUntilTime>2024-01-15T10:30:40.000Z</ValidUntilTime>
        <ItemIdentifier>MIDL_1_1705312215</ItemIdentifier>
        <MonitoredVehicleJourney>
          <LineRef>1</LineRef>
          <DirectionRef>OUTBOUND</DirectionRef>
          <PublishedLineName>1 - Birmingham to Dudley</PublishedLineName>
          <OperatorRef>MIDL</OperatorRef>
          <OriginRef>430003002</OriginRef>
          <OriginName>Birmingham Moor Street</OriginName>
          <DestinationRef>430008001</DestinationRef>
          <DestinationName>Dudley Bus Station</DestinationName>
          <OriginAimedDepartureTime>2024-01-15T08:00:00.000Z</OriginAimedDepartureTime>
          <DestinationAimedArrivalTime>2024-01-15T09:30:00.000Z</DestinationAimedArrivalTime>
          <VehicleLocation>
            <Longitude>-1.8945</Longitude>
            <Latitude>52.4786</Latitude>
          </VehicleLocation>
          <Bearing>45.0</Bearing>
          <Velocity>15.5</Velocity>
          <Occupancy>seatsAvailable</Occupancy>
          <BlockRef>BLOCK_1</BlockRef>
          <VehicleJourneyRef>JOURNEY_MIDL_1000_20240115</VehicleJourneyRef>
          <VehicleRef>MIDL_1000</VehicleRef>
        </MonitoredVehicleJourney>
      </VehicleActivity>
    </VehicleMonitoringDelivery>
  </ServiceDelivery>
</Siri>
```

### GET /health
System health check endpoint.

## Data Elements

### Mandatory BODS Elements
- `Bearing`: Vehicle heading in degrees (0-360)
- `BlockRef`: Operational block identifier
- `DestinationRef`: ATCO stop code for destination
- `DirectionRef`: Journey direction (INBOUND/OUTBOUND)
- `LineRef`: Line identifier
- `MonitoredVehicleJourney`: Complete journey information
- `OperatorRef`: National Operator Code (NOC)
- `OriginRef`: ATCO stop code for origin
- `OriginName`: Origin stop name
- `ProducerRef`: Data producer identifier
- `PublishedLineName`: Public line name/number
- `RecordedAtTime`: When data was recorded (UTC)
- `ResponseTimestamp`: When response was generated (UTC)
- `ValidUntilTime`: When data expires (UTC)
- `VehicleJourneyRef`: Unique journey identifier
- `VehicleLocation`: GPS coordinates (lat/lon)
- `VehicleRef`: Unique vehicle identifier

### Optional Elements
- `DepartureBoardingActivity`: Boarding status
- `DestinationAimedArrivalTime`: Scheduled arrival time
- `DestinationName`: Destination stop name
- `ItemIdentifier`: Unique item identifier
- `Occupancy`: Vehicle fullness status
- `OriginAimedDepartureTime`: Scheduled departure time
- `Velocity`: Vehicle speed (m/s)

## Sample Data

The API generates sample data for Midland Bus routes including:
- Route 1: Birmingham to Dudley
- Route 45: Walsall to Birmingham
- Route 47: West Bromwich to Birmingham

All data uses realistic ATCO codes and follows BODS naming conventions.

## Deployment

### Docker
```bash
cd bods-api
docker-compose up -d
```

### Local Development
```bash
cd bods-api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3002
```

## BODS Registration

To register this feed with BODS:

1. Create an account at the [BODS portal](https://www.bus-data.org.uk/)
2. Upload your SIRI-VM endpoint URL: `https://api.midlandbus.uk/vehicle-monitoring`
3. Provide the check-status URL: `https://api.midlandbus.uk/check-status`
4. Ensure your server allows BODS IP addresses

## Technical Specifications

- **Port**: 3002
- **Protocol**: HTTP GET
- **Data Format**: XML (SIRI-VM schema)
- **Update Frequency**: ≤30 seconds
- **Timezone**: UTC
- **Coordinates**: WGS84 (EPSG:4326)

## Compliance Checklist

- [x] SIRI-VM 2.0 schema compliance
- [x] All mandatory BODS elements present
- [x] Proper XML namespace declarations
- [x] UTC timestamps
- [x] Check-status endpoint
- [x] Valid ATCO codes for stops
- [x] NOC codes for operators
- [x] Data refresh every 30 seconds
- [x] Proper error handling

## Support

For technical issues or questions about this BODS implementation, contact the development team or refer to the [official BODS documentation](https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm).