from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="SiriVM API", description="BODS SiriVM compliant vehicle monitoring API")

# Redis connection
redis_client = redis.Redis(host=os.getenv("REDIS_URL", "redis://redis:6379").split("://")[1].split(":")[0],
                          port=int(os.getenv("REDIS_URL", "redis://redis:6379").split(":")[-1]),
                          decode_responses=True)

# Database connection
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://dashboard_user:dashboard_password@dashboard_db:5433/dashboard"))

# SIRI-VM Data Models
class VehicleLocation(BaseModel):
    longitude: float
    latitude: float

class MonitoredVehicleJourney(BaseModel):
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
    vehicle_location: VehicleLocation
    bearing: float
    velocity: Optional[float] = None
    occupancy: Optional[str] = None
    block_ref: str
    vehicle_journey_ref: str
    vehicle_ref: str

class VehicleActivity(BaseModel):
    recorded_at_time: datetime
    valid_until_time: datetime
    item_identifier: Optional[str] = None
    monitored_vehicle_journey: MonitoredVehicleJourney

class VehicleMonitoringDelivery(BaseModel):
    response_timestamp: datetime
    producer_ref: str
    vehicle_activities: List[VehicleActivity]

class ServiceDelivery(BaseModel):
    response_timestamp: datetime
    producer_ref: str
    vehicle_monitoring_delivery: VehicleMonitoringDelivery

# XML Generation Functions
def create_siri_xml(service_delivery: ServiceDelivery) -> str:
    """Generate SIRI-VM compliant XML"""
    siri = ET.Element("Siri", {
        "version": "2.0",
        "xmlns": "http://www.siri.org.uk/siri",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.siri.org.uk/siri http://www.siri.org.uk/schema/2.0/xsd/siri.xsd"
    })

    service_delivery_elem = ET.SubElement(siri, "ServiceDelivery")
    ET.SubElement(service_delivery_elem, "ResponseTimestamp").text = service_delivery.response_timestamp.isoformat()
    ET.SubElement(service_delivery_elem, "ProducerRef").text = service_delivery.producer_ref

    vehicle_delivery = ET.SubElement(service_delivery_elem, "VehicleMonitoringDelivery")
    ET.SubElement(vehicle_delivery, "ResponseTimestamp").text = service_delivery.vehicle_monitoring_delivery.response_timestamp.isoformat()

    for activity in service_delivery.vehicle_monitoring_delivery.vehicle_activities:
        vehicle_activity = ET.SubElement(vehicle_delivery, "VehicleActivity")

        ET.SubElement(vehicle_activity, "RecordedAtTime").text = activity.recorded_at_time.isoformat()
        ET.SubElement(vehicle_activity, "ValidUntilTime").text = activity.valid_until_time.isoformat()

        if activity.item_identifier:
            ET.SubElement(vehicle_activity, "ItemIdentifier").text = activity.item_identifier

        mvj = ET.SubElement(vehicle_activity, "MonitoredVehicleJourney")

        # Vehicle Journey Identity
        ET.SubElement(mvj, "LineRef").text = activity.monitored_vehicle_journey.line_ref
        ET.SubElement(mvj, "DirectionRef").text = activity.monitored_vehicle_journey.direction_ref

        # Journey Pattern Info
        ET.SubElement(mvj, "PublishedLineName").text = activity.monitored_vehicle_journey.published_line_name

        # Service Info Group
        ET.SubElement(mvj, "OperatorRef").text = activity.monitored_vehicle_journey.operator_ref

        # Vehicle Journey Info
        ET.SubElement(mvj, "OriginRef").text = activity.monitored_vehicle_journey.origin_ref
        ET.SubElement(mvj, "OriginName").text = activity.monitored_vehicle_journey.origin_name
        ET.SubElement(mvj, "DestinationRef").text = activity.monitored_vehicle_journey.destination_ref
        if activity.monitored_vehicle_journey.destination_name:
            ET.SubElement(mvj, "DestinationName").text = activity.monitored_vehicle_journey.destination_name

        if activity.monitored_vehicle_journey.origin_aimed_departure_time:
            ET.SubElement(mvj, "OriginAimedDepartureTime").text = activity.monitored_vehicle_journey.origin_aimed_departure_time.isoformat()
        if activity.monitored_vehicle_journey.destination_aimed_arrival_time:
            ET.SubElement(mvj, "DestinationAimedArrivalTime").text = activity.monitored_vehicle_journey.destination_aimed_arrival_time.isoformat()

        # Journey Progress Info
        location = ET.SubElement(mvj, "VehicleLocation")
        ET.SubElement(location, "Longitude").text = str(activity.monitored_vehicle_journey.vehicle_location.longitude)
        ET.SubElement(location, "Latitude").text = str(activity.monitored_vehicle_journey.vehicle_location.latitude)

        ET.SubElement(mvj, "Bearing").text = str(activity.monitored_vehicle_journey.bearing)

        if activity.monitored_vehicle_journey.velocity:
            ET.SubElement(mvj, "Velocity").text = str(activity.monitored_vehicle_journey.velocity)

        if activity.monitored_vehicle_journey.occupancy:
            ET.SubElement(mvj, "Occupancy").text = activity.monitored_vehicle_journey.occupancy

        # Operational Block Group
        ET.SubElement(mvj, "BlockRef").text = activity.monitored_vehicle_journey.block_ref

        # Operational Info Group
        ET.SubElement(mvj, "VehicleJourneyRef").text = activity.monitored_vehicle_journey.vehicle_journey_ref
        ET.SubElement(mvj, "VehicleRef").text = activity.monitored_vehicle_journey.vehicle_ref

    # Pretty print XML
    rough_string = ET.tostring(siri, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

@app.get("/siri-vm")
async def get_vehicle_monitoring():
    """Get current vehicle positions in SIRI-VM format"""
    try:
        # Get vehicle data from database or cache
        vehicles = get_vehicle_data()

        if not vehicles:
            # Return empty response if no vehicles
            service_delivery = ServiceDelivery(
                response_timestamp=datetime.now(timezone.utc),
                producer_ref="TICKETER_TRACKER",
                vehicle_monitoring_delivery=VehicleMonitoringDelivery(
                    response_timestamp=datetime.now(timezone.utc),
                    producer_ref="TICKETER_TRACKER",
                    vehicle_activities=[]
                )
            )
        else:
            vehicle_activities = []
            for vehicle in vehicles:
                activity = VehicleActivity(
                    recorded_at_time=vehicle['recorded_at_time'],
                    valid_until_time=vehicle['valid_until_time'],
                    item_identifier=vehicle.get('item_identifier'),
                    monitored_vehicle_journey=MonitoredVehicleJourney(
                        line_ref=vehicle['line_ref'],
                        direction_ref=vehicle['direction_ref'],
                        published_line_name=vehicle['published_line_name'],
                        operator_ref=vehicle['operator_ref'],
                        origin_ref=vehicle['origin_ref'],
                        origin_name=vehicle['origin_name'],
                        destination_ref=vehicle['destination_ref'],
                        destination_name=vehicle.get('destination_name'),
                        origin_aimed_departure_time=vehicle.get('origin_aimed_departure_time'),
                        destination_aimed_arrival_time=vehicle.get('destination_aimed_arrival_time'),
                        vehicle_location=VehicleLocation(
                            longitude=vehicle['longitude'],
                            latitude=vehicle['latitude']
                        ),
                        bearing=vehicle['bearing'],
                        velocity=vehicle.get('velocity'),
                        occupancy=vehicle.get('occupancy'),
                        block_ref=vehicle['block_ref'],
                        vehicle_journey_ref=vehicle['vehicle_journey_ref'],
                        vehicle_ref=vehicle['vehicle_ref']
                    )
                )
                vehicle_activities.append(activity)

            service_delivery = ServiceDelivery(
                response_timestamp=datetime.now(timezone.utc),
                producer_ref="TICKETER_TRACKER",
                vehicle_monitoring_delivery=VehicleMonitoringDelivery(
                    response_timestamp=datetime.now(timezone.utc),
                    producer_ref="TICKETER_TRACKER",
                    vehicle_activities=vehicle_activities
                )
            )

        xml_content = create_siri_xml(service_delivery)
        return Response(content=xml_content, media_type="application/xml")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SIRI-VM data: {str(e)}")

@app.post("/vehicle-position")
async def submit_vehicle_position(vehicle_data: dict):
    """Endpoint for dashboard to submit self-tracked vehicle positions"""
    try:
        # Store vehicle position in database
        store_vehicle_position(vehicle_data)
        return {"status": "success", "message": "Vehicle position stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing vehicle position: {str(e)}")

@app.delete("/vehicle-positions")
async def delete_vehicle_positions(
    vehicle_ref: Optional[str] = None,
    before_timestamp: Optional[str] = None,
    operator_ref: Optional[str] = None,
    days_old: Optional[int] = None
):
    """Delete vehicle positions with optional filters"""
    try:
        query = "DELETE FROM vehicle_positions WHERE 1=1"
        params = []

        if vehicle_ref:
            query += " AND vehicle_ref = %s"
            params.append(vehicle_ref)

        if before_timestamp:
            # Parse timestamp string to datetime
            try:
                cutoff = datetime.fromisoformat(before_timestamp.replace('Z', '+00:00'))
                query += " AND recorded_at_time < %s"
                params.append(cutoff)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")
        elif days_old:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
            query += " AND recorded_at_time < %s"
            params.append(cutoff)

        if operator_ref:
            query += " AND operator_ref = %s"
            params.append(operator_ref)

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params)
            deleted_count = cur.rowcount
            conn.commit()

        return {
            "status": "success",
            "deleted": deleted_count,
            "filters": {
                "vehicle_ref": vehicle_ref,
                "before_timestamp": before_timestamp,
                "operator_ref": operator_ref,
                "days_old": days_old
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting positions: {str(e)}")


@app.delete("/tracking-sessions/{session_id}")
async def delete_tracking_session(session_id: int):
    """Delete a specific tracking session and its positions"""
    try:
        # Get session details first
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tracking_sessions WHERE id = %s", (session_id,))
            session = cur.fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete positions within session timeframe
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM vehicle_positions
                WHERE vehicle_ref = %s
                AND recorded_at_time BETWEEN %s AND %s
            """, (
                session['vehicle_ref'],
                session['start_time'],
                session['end_time'] or datetime.now(timezone.utc)
            ))
            positions_deleted = cur.rowcount

            # Delete session
            cur.execute("DELETE FROM tracking_sessions WHERE id = %s", (session_id,))

            conn.commit()

        return {
            "status": "success",
            "deleted_session": True,
            "deleted_positions": positions_deleted,
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.delete("/bulk-cleanup")
async def bulk_cleanup(
    days_old: int = 30,
    vehicle_ref: Optional[str] = None,
    operator_ref: Optional[str] = None
):
    """Bulk cleanup of old tracking data"""
    try:
        conn = get_db_connection()
        deleted_positions = 0
        deleted_sessions = 0

        with conn.cursor() as cur:
            # Delete old positions
            pos_query = "DELETE FROM vehicle_positions WHERE recorded_at_time < %s"
            pos_params = [datetime.now(timezone.utc) - timedelta(days=days_old)]

            if vehicle_ref:
                pos_query += " AND vehicle_ref = %s"
                pos_params.append(vehicle_ref)

            if operator_ref:
                pos_query += " AND operator_ref = %s"
                pos_params.append(operator_ref)

            cur.execute(pos_query, pos_params)
            deleted_positions = cur.rowcount

            # Delete old sessions
            sess_query = "DELETE FROM tracking_sessions WHERE start_time < %s"
            sess_params = [datetime.now(timezone.utc) - timedelta(days=days_old)]

            if vehicle_ref:
                sess_query += " AND vehicle_ref = %s"
                sess_params.append(vehicle_ref)

            cur.execute(sess_query, sess_params)
            deleted_sessions = cur.rowcount

            conn.commit()

        return {
            "status": "success",
            "deleted_positions": deleted_positions,
            "deleted_sessions": deleted_sessions,
            "days_old": days_old,
            "filters": {
                "vehicle_ref": vehicle_ref,
                "operator_ref": operator_ref
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during bulk cleanup: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

def get_vehicle_data():
    """Get vehicle data from database"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM vehicle_positions
                WHERE recorded_at_time > NOW() - INTERVAL '5 minutes'
                ORDER BY recorded_at_time DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def store_vehicle_position(data):
    """Store vehicle position in database"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vehicle_positions (
                    vehicle_ref, line_ref, direction_ref, published_line_name,
                    operator_ref, origin_ref, origin_name, destination_ref,
                    destination_name, longitude, latitude, bearing, velocity,
                    occupancy, block_ref, vehicle_journey_ref, recorded_at_time,
                    valid_until_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_ref, recorded_at_time)
                DO UPDATE SET
                    longitude = EXCLUDED.longitude,
                    latitude = EXCLUDED.latitude,
                    bearing = EXCLUDED.bearing,
                    velocity = EXCLUDED.velocity,
                    occupancy = EXCLUDED.occupancy,
                    valid_until_time = EXCLUDED.valid_until_time
            """, (
                data['vehicle_ref'], data['line_ref'], data['direction_ref'],
                data['published_line_name'], data['operator_ref'], data['origin_ref'],
                data['origin_name'], data['destination_ref'], data.get('destination_name'),
                data['longitude'], data['latitude'], data['bearing'],
                data.get('velocity'), data.get('occupancy'), data['block_ref'],
                data['vehicle_journey_ref'], data['recorded_at_time'], data['valid_until_time']
            ))
            conn.commit()
    except Exception as e:
        print(f"Database error storing position: {e}")
        raise
    finally:
        if conn:
            conn.close()