# BODS API

A fully BODS (Bus Open Data Service) compliant API implementing the SIRI-VM (Service Interface for Real-time Information - Vehicle Monitoring) standard for real-time bus location data.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
cd bods-api
docker-compose up -d
```

The API will be available at `http://localhost:3002`

### Local Development

```bash
cd bods-api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3002
```

## 📋 BODS Compliance

This implementation is fully compliant with the UK Department for Transport's BODS requirements:

- ✅ SIRI-VM 2.0 schema compliance
- ✅ All mandatory BODS elements present
- ✅ Proper XML namespace declarations
- ✅ UTC timestamps with ISO 8601 formatting
- ✅ Check-status endpoint for service monitoring
- ✅ Valid ATCO codes for stops
- ✅ NOC codes for operators
- ✅ Data refresh every 30 seconds
- ✅ Proper error handling

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and available endpoints |
| `/check-status` | GET | **BODS Required** - Service status check |
| `/vehicle-monitoring` | GET | **Main Data** - Real-time vehicle positions |
| `/health` | GET | System health check |
| `/docs` | GET | Interactive API documentation |

## 📊 Sample Usage

### Check Service Status
```bash
curl http://localhost:3002/check-status
```

### Get All Vehicle Data
```bash
curl http://localhost:3002/vehicle-monitoring
```

### Filter by Line
```bash
curl "http://localhost:3002/vehicle-monitoring?LineRef=1"
```

### Filter by Operator
```bash
curl "http://localhost:3002/vehicle-monitoring?OperatorRef=MIDL"
```

## 🏗️ Architecture

```
bods-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic data models
│   ├── data_generator.py # Sample vehicle data
│   └── xml_generator.py  # SIRI-VM XML generation
├── docs/
│   └── README.md        # Detailed documentation
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Docker orchestration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🗂️ Data Model

### Mandatory BODS Elements
- `Bearing` - Vehicle heading (0-360°)
- `BlockRef` - Operational block identifier
- `DestinationRef` - ATCO stop code for destination
- `DirectionRef` - Journey direction (INBOUND/OUTBOUND)
- `LineRef` - Line identifier
- `OperatorRef` - National Operator Code (NOC)
- `OriginRef` - ATCO stop code for origin
- `PublishedLineName` - Public line name/number
- `VehicleLocation` - GPS coordinates (lat/lon)
- `VehicleRef` - Unique vehicle identifier
- `RecordedAtTime` - Data timestamp (UTC)
- `ValidUntilTime` - Data expiry time (UTC)

### Sample Routes
- **Route 1**: Birmingham Moor Street → Dudley Bus Station
- **Route 45**: Walsall Bus Station → Birmingham Moor Street
- **Route 47**: West Bromwich Bus Station → Birmingham Moor Street

## 🔧 Configuration

### Environment Variables
- `ENVIRONMENT` - Set to `development` for debug mode

### Docker Compose Override
```yaml
version: '3.8'
services:
  bods-api:
    environment:
      - ENVIRONMENT=production
    ports:
      - "3002:3002"
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:3002/health
```

### Validate XML Response
```bash
curl -s http://localhost:3002/vehicle-monitoring | xmllint --format -
```

### Test BODS Compliance
```bash
# Check status endpoint
curl -s http://localhost:3002/check-status | grep -q "<Status>true</Status>" && echo "✅ Status OK"

# Check vehicle data
curl -s http://localhost:3002/vehicle-monitoring | grep -q "<VehicleActivity>" && echo "✅ Vehicle data OK"
```

## 📚 Documentation

- [API Documentation](docs/README.md) - Comprehensive technical documentation
- [BODS Technical Guidance](https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm) - Official DfT specification
- [SIRI Standards](https://github.com/SIRI-CEN/SIRI) - CEN SIRI documentation

## 🚀 Deployment

### Production Deployment

1. **Build the image:**
   ```bash
   docker build -t midland-bus-bods-api .
   ```

2. **Run with docker-compose:**
   ```bash
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f bods-api
   ```

### Cloud Deployment

The API is designed to work with Cloudflare tunnels for public access:

- **Local Development**: `http://localhost:3002`
- **Production**: `https://api.midlandbus.uk` (via Cloudflare tunnel)

## 🔒 Security

- No authentication required (as per BODS specification)
- IP whitelisting recommended for production
- Rate limiting should be implemented at infrastructure level
- HTTPS required for production deployments

## 🤝 BODS Registration

To register with the Bus Open Data Service:

1. Create account at [BODS Portal](https://www.bus-data.org.uk/)
2. Provide endpoint URLs:
   - Vehicle Monitoring: `https://api.midlandbus.uk/vehicle-monitoring`
   - Check Status: `https://api.midlandbus.uk/check-status`
3. Allow BODS IP addresses in firewall
4. Submit for validation

## 📈 Monitoring

### Key Metrics
- Response time < 1 second
- Uptime > 99.9%
- Data freshness < 30 seconds
- XML schema validation

### Logging
- Request/response logging
- Error tracking
- Performance metrics

## 🐛 Troubleshooting

### Common Issues

**Port 3002 already in use:**
```bash
lsof -i :3002
kill -9 <PID>
```

**XML parsing errors:**
```bash
curl -s http://localhost:3002/vehicle-monitoring | python -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.stdin); print('Valid XML')"
```

**Container not starting:**
```bash
docker-compose logs bods-api
```

## 📞 Support

- **Technical Issues**: Check logs and validate XML output
- **BODS Compliance**: Refer to official DfT documentation
- **API Questions**: Review the `/docs` endpoint

## 📄 License

This implementation follows the BODS technical guidance and SIRI standards. Ensure compliance with DfT terms when deploying to production.

---

**Version**: 1.0.0
**SIRI Version**: 2.0
**BODS Profile**: Department for Transport SIRI-VM Profile
