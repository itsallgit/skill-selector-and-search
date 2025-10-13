# Configuration

The application uses environment variables in `backend/.env`. 

## Setup Methods

### Method 1: Interactive Setup (Recommended)
Run the setup script which will:
- Discover available AWS profiles
- List S3 Vector buckets and standard S3 buckets
- Prompt for selections
- Auto-generate `.env` file

```bash
./skill-search-setup.sh
```

### Method 2: Manual Configuration
Copy the template and edit values:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your specific values
```

## Task-Based AWS Configuration

Configure AWS access by task. Each task can use a different AWS account/profile:

```bash
# =============================================================================
# Default AWS Configuration (fallback for all tasks)
# =============================================================================
AWS_PROFILE=default
AWS_REGION=ap-southeast-2

# =============================================================================
# Task 1: Embedding Generation (AWS Bedrock)
# Override only if Bedrock is in a different account
# =============================================================================
EMBEDDING_AWS_PROFILE=profileA
EMBEDDING_AWS_REGION=us-east-1
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024

# =============================================================================
# Task 2: Vector Index Querying (AWS S3 Vectors)
# Override only if vector index is in a different account
# =============================================================================
VECTOR_AWS_PROFILE=profileB
VECTOR_AWS_REGION=ap-southeast-2
VECTOR_BUCKET=<your-vector-bucket-name>  # e.g., skills-vectors-XXXXXXXXXX
VECTOR_INDEX=skills-index

# =============================================================================
# Task 3: Data Ingestion (AWS S3 Read)
# Override only if S3 data bucket is in a different account
# =============================================================================
INGESTION_AWS_PROFILE=profileC
INGESTION_AWS_REGION=ap-southeast-2
INGESTION_BUCKET=<your-ingestion-bucket-name>  # e.g., skills-selector-XXXXXXXXXX
```

**For Single Account**: Just set `AWS_PROFILE` and `AWS_REGION`. Comment out or remove task-specific overrides.

**For Multi-Account**: Set task-specific profiles as shown above.

**Note**: 
- Vector buckets are created via "Skill Embeddings > Provision Vector Bucket & Index"
- Ingestion buckets are created via "Skill Selector" deployment
- Use the setup script to automatically discover and select from available buckets

## Scoring Configuration

Customize the ranking algorithm:

```bash
# Level weights
LEVEL_WEIGHT_L1=0.1   # Categories - broad context
LEVEL_WEIGHT_L2=0.2   # Sub-categories
LEVEL_WEIGHT_L3=0.5   # Generic skills - MOST IMPORTANT
LEVEL_WEIGHT_L4=0.3   # Technologies/tools

# Rating multipliers (exponential proficiency boost)
RATING_MULTIPLIER_1=1.0   # Beginner
RATING_MULTIPLIER_2=2.0   # Intermediate
RATING_MULTIPLIER_3=4.0   # Advanced

# Transfer bonus (partial credit for related tech)
TRANSFER_BONUS_PER_TECH=0.02
TRANSFER_BONUS_CAP=0.15

# Score buckets (percentage thresholds)
EXCELLENT_MIN_SCORE=80
STRONG_MIN_SCORE=60
GOOD_MIN_SCORE=40
```

## Display Configuration

Control UI behavior:

```bash
TOP_USERS_COUNT=5      # Always show top N users
USERS_PER_PAGE=10      # Pagination size
```
