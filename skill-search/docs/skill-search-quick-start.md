# Quick Start

## Automated Setup (Recommended)

The `skill-search-setup.sh` script handles everything:

```bash
cd skill-search
./skill-search-setup.sh
```

**What the script does:**
1. ✓ Checks Docker is installed and running
2. ✓ Lists available AWS profiles and prompts for selection
3. ✓ Validates AWS credentials
4. ✓ Configures the application with selected profile
5. ✓ Copies shared CSS files
6. ✓ Offers to ingest user data from S3
7. ✓ Builds and starts Docker containers (backend + frontend)
8. ✓ Shows you how to access the application

**First-time setup** takes 2-3 minutes (building Docker images).

**Subsequent runs** take only seconds (uses cached images).

## Access the Application

After setup completes:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Testing

```bash
# Quick API validation
cd skill-search/scripts
./test_api.sh

# Comprehensive tests
python test_api.py
```

## Monitoring

```bash
# Watch logs in real-time (both services):
docker-compose logs -f

# Watch just backend:
docker-compose logs -f backend

# Watch just frontend:
docker-compose logs -f frontend

# Check resource usage:
docker stats
```
