# Configuration

Configuration is managed through the setup script which generates a configuration file.

## Configuration Process

Run the setup script to configure AWS profiles and vector bucket:

```bash
./skill-embeddings-setup.sh
```

Or from the project menu:
- Main Menu → Skill Embeddings → Setup & Run Embeddings

The setup script will:
1. List available AWS profiles
2. Prompt for profile selection (same profile for both services, or separate)
3. Auto-detect regions for selected profiles
4. List available S3 Vector buckets
5. Generate `skill-embeddings-config.json`

## Generated Configuration File

The setup script creates `skill-embeddings-config.json`:

```json
{
  "bedrock_profile": "your-bedrock-profile",
  "bedrock_region": "us-east-1",
  "s3vectors_profile": "your-s3-profile",
  "s3vectors_region": "ap-southeast-2",
  "vector_bucket": "skills-vectors-xxxxx",
  "vector_index": "skills-index"
}
```

**Note**: This file is gitignored and contains your specific AWS profile names.

**For Single Account**: The setup will use the same profile for both services.

**For Multi-Account**: The setup will prompt for separate profiles.

## Static Configuration (in Python scripts)

The following settings are hardcoded in the Python scripts and don't require changes:

### Embedding Model Configuration

```python
# Embedding Model Configuration (static)
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIM = 1024
DISTANCE_METRIC = "cosine"
```

**Note**: These must match the S3 Vector Index configuration (set during deployment).

## File Paths

```python
# File Paths (relative to script location)
SKILLS_MASTER_PATH = "../../data/skills-master.json"      # Input
EMBEDDINGS_OUTPUT_PATH = "../../data/skill-embeddings.jsonl"  # Output
```

## Processing Configuration

```python
# Processing Configuration
EMBEDDING_BATCH_SIZE = 25      # Skills per Bedrock API call
MAX_VECTORS_PER_UPLOAD = 50    # Vectors per S3 Vectors API call
```

**Tuning**:
- Larger batches = fewer API calls = faster processing
- Smaller batches = more granular error handling
- AWS service limits may restrict maximum batch sizes

## Cost Optimization

The script performs **incremental updates** to minimize Bedrock costs:
- Compares current skills with `skill-embeddings.jsonl`
- Only generates embeddings for new or changed skills
- Full re-embedding only needed if model or configuration changes

To force full re-embedding: Delete `skill-embeddings.jsonl` before running.
