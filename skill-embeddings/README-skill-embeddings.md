# Skill Embeddings

Generates semantic embeddings for hierarchical skills and uploads them to AWS S3 Vector Index for semantic search capabilities.

## Documentation

- [Overview](docs/skill-embeddings-overview.md) - What it does and key capabilities
- [Architecture](docs/skill-embeddings-architecture.md) - Processing pipeline and AWS services
- [Prerequisites](docs/skill-embeddings-prerequisites.md) - Required software and AWS access
- [Configuration](docs/skill-embeddings-configuration.md) - AWS profiles and processing options
- [Quick Start](docs/skill-embeddings-quick-start.md) - Deploy and generate embeddings
- [Development](docs/skill-embeddings-development.md) - Script architecture and customization
- [Implementation](docs/skill-embeddings-implementation.md) - Algorithms and design decisions
- [Deployment](docs/skill-embeddings-deployment.md) - Infrastructure and production setup

## Quick Reference

```bash
# Deploy infrastructure (one-time)
cd infra && ./deploy-skill-embeddings.sh

# Generate embeddings
cd scripts && python3 skill-embeddings.py

# Test search
python3 test-skill-embeddings.py

# View embeddings file
cat ../../data/skill-embeddings.jsonl | head -5 | jq '.'
```

## What It Does

Transforms hierarchical skill taxonomy (`skills-master.json`) into semantic vectors for search:

1. **Flattens** skills hierarchy while preserving relationships
2. **Detects** changes for incremental updates (cost optimization)
3. **Generates** embeddings using AWS Bedrock Titan V2
4. **Saves** to persistent JSONL format
5. **Uploads** to S3 Vector Index for fast semantic search

Each skill becomes searchable with rich metadata including title, hierarchy level, parent relationships, and full ancestry.

## When to Use

Run the embeddings generator when:
- Setting up the system for the first time
- skills-master.json is updated (new/changed skills)
- Switching embedding models or dimensions
- Recreating vector index

The incremental update feature makes frequent re-runs efficient by only processing changes.
