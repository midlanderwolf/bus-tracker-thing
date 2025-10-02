# Ticketer Tracker

A bus tracking system with BODS SiriVM API compliance and self-tracking dashboard.

## Architecture

- **API Service** (Port 3002): FastAPI service providing BODS SiriVM compliant vehicle position data
- **Dashboard** (Port 3001): Django web application for self-tracking and map visualization
- **Databases**:
  - Port 5432: Existing bustimes.org database (external connection)
  - Port 5433: New dashboard/API database

## Features

- BODS SiriVM API compliance for vehicle position data
- Self-tracking via browser geolocation
- Single sign-on with existing bustimes.org accounts
- Real-time map visualization with Leaflet
- Docker containerization

## Quick Start

1. **Prerequisites:**
   - Ensure your existing bustimes.org database is running on port 5432
   - Default credentials: postgres/postgres

2. **Clone and setup:**
   ```bash
   git clone <repository>
   cd ticketer-tracker
   ```

3. **Start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Run database migrations:**
   ```bash
   # Dashboard migrations
   docker-compose exec dashboard python manage.py migrate
   ```

5. **Migrate users from bustimes.org:**
   ```bash
   # Analyze existing database
   docker-compose exec dashboard python ../migrate_users.py --analyze

   # Perform migration
   docker-compose exec dashboard python ../migrate_users.py
   ```

5. **Access the applications:**
   - Dashboard: http://localhost:3001
   - API: http://localhost:3002
   - SIRI-VM endpoint: http://localhost:3002/siri-vm

## API Endpoints

### SIRI-VM API (Port 3002)

- `GET /siri-vm` - Get current vehicle positions in SIRI-VM XML format
- `POST /vehicle-position` - Submit vehicle position data
- `GET /health` - Health check

### Dashboard API (Port 3001)

- `GET /api/vehicles/` - Get current vehicle positions (JSON)
- `POST /api/start-tracking/` - Start self-tracking session
- `POST /api/update-position/` - Update current position
- `POST /api/stop-tracking/` - Stop tracking session

## User Authentication

Users can log in with their existing bustimes.org email and password. The system automatically migrates user accounts to the new database while maintaining password compatibility. The authentication uses email as the username field (matching bustimes.org behavior).

## Development

### Prerequisites

- Docker and Docker Compose
- PostgreSQL databases on ports 5432 and 5433

### Project Structure

```
ticketer-tracker/
├── api/                    # FastAPI SIRI-VM service
│   ├── main.py            # Main API application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # API container
├── dashboard/             # Django dashboard
│   ├── config/            # Django settings
│   ├── tracker/           # Main app
│   ├── templates/         # HTML templates
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Dashboard container
├── docker-compose.yml     # Container orchestration
├── init-dashboard.sql    # Database initialization
├── migrate_users.py       # User migration script
└── README.md             # This file
```

### Environment Variables

The application uses these environment variables (with defaults):

- `DATABASE_URL` - Dashboard database connection
- `BUSTIMES_DATABASE_URL` - Bustimes.org database connection
- `REDIS_URL` - Redis connection for caching
- `SECRET_KEY` - Django secret key
- `DEBUG` - Django debug mode

## SIRI-VM Compliance

The API implements the Department for Transport's BODS SIRI-VM profile with mandatory elements:

- Vehicle location (longitude/latitude)
- Bearing and velocity
- Route and operator information
- Timestamps in UTC
- XML response format

## Self-Tracking

Users can track their position using browser geolocation:

1. Login with existing credentials
2. Enter vehicle reference
3. Start tracking to appear on the map
4. Position updates sent to API every few seconds
5. Stop tracking when finished

## Contributing

1. Follow the AGENTS.md guidelines for code style
2. Test with both databases running
3. Ensure SIRI-VM compliance for API changes
4. Update documentation for new features

## License

See LICENSE file for details.