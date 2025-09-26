from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from datetime import datetime
import logging
from .data_generator import vehicle_generator
from .xml_generator import create_siri_vehicle_monitoring_response, create_check_status_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Midland Bus BODS API",
    description="Bus Open Data Service (BODS) compliant API for real-time vehicle monitoring using SIRI-VM standard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Service start time for status reporting
SERVICE_START_TIME = datetime.utcnow()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
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


@app.get("/check-status", response_class=PlainTextResponse, tags=["BODS Compliance"])
async def check_status():
    """
    BODS Check Status endpoint

    Returns the current status of the SIRI-VM service as required by BODS.
    This endpoint must respond to confirm the service is operational.
    """
    try:
        logger.info("Check status request received")
        xml_response = create_check_status_response(
            status=True,
            service_started_time=SERVICE_START_TIME
        )
        return xml_response
    except Exception as e:
        logger.error(f"Error in check_status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/vehicle-monitoring", response_class=PlainTextResponse, tags=["Vehicle Monitoring"])
async def vehicle_monitoring(
    request: Request,
    LineRef: str | None = Query(None),
    OperatorRef: str | None = Query(None),
    VehicleRef: str | None = Query(None),
    MaximumNumberOfVehicles: int | None = Query(None)
):
    """
    SIRI-VM Vehicle Monitoring endpoint

    Returns real-time vehicle position and journey information for all active vehicles.

    Query Parameters:
    - LineRef: Filter by specific line (optional)
    - OperatorRef: Filter by operator (optional)
    - VehicleRef: Filter by specific vehicle (optional)
    - MaximumNumberOfVehicles: Limit number of results (optional)

    Returns SIRI-VM compliant XML response with vehicle monitoring data.
    """
    try:
        client_host = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        logger.info(f"Vehicle monitoring request from {client_host}")

        # Get current vehicle data
        vehicles_data = vehicle_generator.get_vehicle_data()

        # Apply filters if provided
        if LineRef:
            vehicles_data = [v for v in vehicles_data if v.line_ref == LineRef]

        if OperatorRef:
            vehicles_data = [v for v in vehicles_data if v.operator_ref == OperatorRef]

        if VehicleRef:
            vehicles_data = [v for v in vehicles_data if v.vehicle_ref == VehicleRef]

        if MaximumNumberOfVehicles:
            vehicles_data = vehicles_data[:MaximumNumberOfVehicles]

        # Generate SIRI-VM XML response
        xml_response = create_siri_vehicle_monitoring_response(
            vehicles=vehicles_data,
            producer_ref="MIDLANDBUS"
        )

        logger.info(f"Returning data for {len(vehicles_data)} vehicles")
        return xml_response

    except Exception as e:
        logger.error(f"Error in vehicle_monitoring: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BODS API",
        "version": "1.0.0"
    }


# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return PlainTextResponse(
        content="Internal server error",
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)