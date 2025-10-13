# Architecture

## Backend (FastAPI)
- **Framework**: FastAPI with async operations
- **Embeddings**: AWS Bedrock Titan Embeddings V2 (1024 dimensions)
- **Vector Search**: AWS S3 Vectors with cosine distance
- **Data Access**: Repository pattern for future DB migration
- **Configuration**: Task-based AWS profiles with automatic fallback
- **Multi-Account Support**: Flexible configuration for split AWS resources

## Frontend (React)
- **Framework**: React 18 with React Router
- **Styling**: Shared CSS with skill-selector app
- **API Communication**: Axios for HTTP requests
- **Hot Reload**: Development mode with Docker volumes

## AWS Configuration Strategy

The application supports both **single-account** and **multi-account** AWS setups:

### Single Account (Recommended)
When all AWS resources are in one account, simply configure:
```bash
AWS_PROFILE=my-account
AWS_REGION=ap-southeast-2
```

### Multi-Account (Advanced)
When resources are split across accounts, override specific tasks:
- **Embedding Generation** (AWS Bedrock): Uses `EMBEDDING_AWS_PROFILE`
- **Vector Search** (S3 Vectors): Uses `VECTOR_AWS_PROFILE`
- **Data Ingestion** (S3): Uses `INGESTION_AWS_PROFILE`

Each task-specific profile falls back to `AWS_PROFILE` if not specified.

**Example Multi-Account Setup:**
```bash
AWS_PROFILE=default
AWS_REGION=ap-southeast-2

# Bedrock in account 1
EMBEDDING_AWS_PROFILE=bedrock-account
EMBEDDING_AWS_REGION=us-east-1

# Vector index and data in account 2
VECTOR_AWS_PROFILE=storage-account
VECTOR_AWS_REGION=ap-southeast-2
INGESTION_AWS_PROFILE=storage-account
```
