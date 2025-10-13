# Prerequisites

## Required Software
- Python 3.8 or higher
- AWS CLI configured with profiles

## Required Data
- `data/skills-master.json` - Hierarchical skill taxonomy
- S3 Vector Index (created by deploy-skill-embeddings.sh)

## AWS Access Requirements

### AWS Bedrock
- Access to `amazon.titan-embed-text-v2:0` model
- Typically available in `us-east-1` region
- Required permission: `bedrock:InvokeModel`

### AWS S3 Vectors
- Pre-created vector bucket and index
- Required permissions:
  - `s3vectors:GetIndex` - Verify index exists
  - `s3vectors:PutVectors` - Upload embeddings
  - `s3:PutObject` - Write to vector bucket

## Setup Steps

1. **Create Vector Index** (one-time):
   
   From the project menu:
   - Main Menu → Skill Embeddings → Provision Vector Bucket & Index
   
   Or via command line:
   ```bash
   cd skill-embeddings/infra
   ./deploy-skill-embeddings.sh
   ```

2. **Install Python Dependencies**:
   ```bash
   cd skill-embeddings
   pip install -r requirements.txt
   ```

3. **Configure AWS Profiles and Vector Bucket**:
   
   From the project menu:
   - Main Menu → Skill Embeddings → Setup & Run Embeddings
   
   Or via command line:
   ```bash
   cd skill-embeddings
   ./skill-embeddings-setup.sh
   ```
   
   The setup script will:
   - List your available AWS profiles
   - Prompt you to select profiles for Bedrock and S3 Vectors
   - Auto-detect regions for selected profiles
   - List available vector buckets
   - Generate `skill-embeddings-config.json` with your configuration
