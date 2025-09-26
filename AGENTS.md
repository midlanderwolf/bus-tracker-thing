# AGENTS.md

## Build/Lint/Test Commands
- **Build**: `docker-compose build` (Docker) or `pip install -r requirements.txt` (local)
- **Run**: `docker-compose up` or `python manage.py runserver`
- **Test**: `python manage.py test`
- **Single test**: `python manage.py test tracker.tests.TestClass.test_method`
- **Migrations**: `python manage.py makemigrations && python manage.py migrate`
- **Tunnel Setup**: `./setup-tunnels.sh` (Cloudflare tunnels for midlandbus.uk domains)
- **Tunnel Test**: `./test-tunnels.sh` (Test local services and tunnel connectivity)
- **BODS API Build**: `cd bods-api && docker-compose build`
- **BODS API Run**: `cd bods-api && docker-compose up -d`
- **BODS API Test**: `curl http://localhost:3002/check-status`

## Code Style Guidelines

### Python/Django Style
- **Imports**: Standard library first, then third-party, then local imports
- **Formatting**: 4 spaces indentation, 88 char line length (PEP 8)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Docstrings**: Use triple quotes for module/class/function docs
- **Models**: Use verbose field names, add help_text for complex fields

### Django Specific
- **Models**: Define __str__ methods, use Meta classes for ordering/indexes
- **Views**: Use class-based views when possible, handle exceptions properly
- **URLs**: Use path() over url(), include app namespaces
- **Settings**: Use python-decouple for environment variables

### FastAPI Style (BODS API)
- **Models**: Use Pydantic BaseModel with Field descriptions
- **Endpoints**: Descriptive docstrings, proper status codes
- **Error Handling**: Use HTTPException with appropriate status codes
- **Validation**: Leverage Pydantic validators for complex logic

### General
- **Error Handling**: Try/catch blocks, log errors appropriately
- **Logging**: Use Python logging module, configure appropriate levels
- **Security**: Validate inputs, use Django's security features
- **Performance**: Use select_related/prefetch_related for optimization