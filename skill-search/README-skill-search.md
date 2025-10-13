# Skill Search

A full-stack web application for finding users by skills using natural language semantic search. Powered by AWS Bedrock embeddings and intelligent ranking algorithms.

## Documentation

- [Overview](docs/skill-search-overview.md) - Key capabilities and features
- [Architecture](docs/skill-search-architecture.md) - System design and AWS configuration strategy
- [Prerequisites](docs/skill-search-prerequisites.md) - Required software and AWS access
- [Configuration](docs/skill-search-configuration.md) - Environment variables and customization
- [Quick Start](docs/skill-search-quick-start.md) - Get up and running in minutes
- [Development](docs/skill-search-development.md) - Manual setup and project structure
- [Implementation](docs/skill-search-implementation.md) - Scoring algorithm and API details
- [Deployment](docs/skill-search-deployment.md) - Docker deployment and production considerations

## Quick Reference

```bash
# One-click setup
./skill-search-setup.sh

# Access the application
open http://localhost:3000

# Run API tests
cd scripts && ./test_api.sh

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## What It Does

Enter natural language queries like **"AWS Lambda and serverless architecture"** to find users with matching skills. The application uses semantic search to understand meaning, not just keywords, and ranks users based on:

- **Skill relevance** to your query (vector similarity)
- **Skill hierarchy** (prioritizes core competencies over tools)
- **User proficiency** (advanced users rank higher)
- **Transfer bonuses** (recognizes related technology experience)

Results are organized into score buckets (Excellent, Strong, Good, Other) with the top 5 matches always displayed.
