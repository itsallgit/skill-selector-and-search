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

Enter natural language queries like **"AWS Lambda and serverless architecture"** to find users with matching skills. The application uses semantic search to understand meaning, not just keywords, and ranks users based on two key dimensions:

### Two-Dimensional Scoring

**Coverage** (Breadth) - Measures how many relevant skills the user possesses
- Each matched skill contributes based on its similarity to the query
- Higher similarity skills contribute more (similarity²)
- Displayed as a percentage of maximum possible coverage

**Expertise** (Depth) - Measures proficiency level across matched skills
- Beginner (1): 1.0× multiplier
- Intermediate (2): 3.0× multiplier  
- Advanced (3): 6.0× multiplier
- Displayed as human-readable labels: Beginner, Early Career, Intermediate, Advanced, Expert

**Final Ranking** = Coverage × Expertise

This approach ensures both skill breadth and proficiency depth matter. A user with deep expertise in one highly relevant skill can rank higher than a user with many weakly relevant skills.

Results are organized into score buckets (Excellent, Strong, Good, Other) with the top 5 matches always displayed.
