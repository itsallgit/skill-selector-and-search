# Deployment

## Docker Deployment (Recommended)

### Using Setup Script
```bash
cd skill-search
./skill-search-setup.sh
```

The script handles:
- Docker validation
- AWS configuration
- Container orchestration
- User data ingestion

### Manual Docker Commands
```bash
# Build and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild after code changes
docker-compose up -d --build backend
```

## Production Considerations

### Environment Configuration
- Store `.env` file securely (never commit to git)
- Use AWS IAM roles instead of profiles where possible
- Consider secrets management (AWS Secrets Manager, etc.)

### Performance
- Backend is async-capable (handles concurrent requests efficiently)
- Consider scaling with multiple backend replicas
- Monitor vector search latency (Bedrock and S3 Vectors)
- User data is in-memory (fast but limited by RAM)

### Monitoring
- Health endpoint: `/api/health` for container health checks
- Stats endpoint: `/api/stats` for application metrics
- Docker logs for debugging
- Consider adding APM (Application Performance Monitoring)

### Security
- Frontend proxy configuration prevents CORS issues
- AWS credentials via profiles (not hardcoded)
- No authentication implemented (add if needed for production)
- Consider rate limiting for public deployments

## Infrastructure Requirements

### AWS Resources
- **Bedrock access** in us-east-1 (or configured region)
- **S3 Vectors** with pre-built index
- **S3 bucket** with user data JSON

### Compute Resources
- **Backend**: ~512MB RAM, 0.5 CPU
- **Frontend**: ~256MB RAM, 0.25 CPU
- Docker Desktop or container orchestration platform

### Network
- Ports 3000 (frontend) and 8000 (backend)
- Inter-container communication via Docker network
- Outbound access to AWS services
