# Prerequisites

## Required Software
- Docker Desktop installed and running
- AWS CLI configured with at least one profile

## AWS Access Requirements

Access to the following AWS services:
- **AWS Bedrock** (for embeddings) - typically in `us-east-1`
- **AWS S3 Vectors** (for vector index) - any region
- **S3 bucket** with user data (`skills-selector-*`)

## AWS Permissions

Your AWS profile needs permissions for:
- `bedrock:InvokeModel` - For generating embeddings
- `s3vectors:QueryVectors` - For searching vector index
- `s3vectors:GetIndex` - For verifying index configuration
- `s3:GetObject` - For reading user data
- `s3:ListBucket` - For finding data buckets
