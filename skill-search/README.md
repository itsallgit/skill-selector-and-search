# Skills Search Application

A full-stack web application for finding users by skills using natural language semantic search.

## Features

- **Natural Language Search**: Enter queries like "AWS Lambda and serverless architecture" to find relevant users
- **Vector-based Matching**: Uses AWS Bedrock Titan Embeddings V2 for semantic skill matching
- **Smart Ranking Algorithm**: 
  - Weighted scoring across skill hierarchy levels (L1-L4)
  - Exponential rating multipliers for user proficiency
  - Transfer bonus for related technologies under different categories
- **Intuitive UI**:
  - Top 5 matches always displayed
  - Expandable score buckets (Excellent, Strong, Good, Other)
  - User detail pages with full skill breakdown
- **Docker Deployment**: One-click setup with `./setup.sh`

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async operations
- **Embeddings**: AWS Bedrock Titan Embeddings V2 (1024 dimensions)
- **Vector Search**: AWS S3 Vectors with cosine distance
- **Data Access**: Repository pattern for future DB migration
- **Configuration**: Task-based AWS profiles with automatic fallback
- **Multi-Account Support**: Flexible configuration for split AWS resources

### Frontend (React)
- **Framework**: React 18 with React Router
- **Styling**: Shared CSS with skill-selector app
- **API Communication**: Axios for HTTP requests
- **Hot Reload**: Development mode with Docker volumes

### AWS Configuration Strategy

The application supports both **single-account** and **multi-account** AWS setups:

#### Single Account (Recommended)
When all AWS resources are in one account, simply configure:
```bash
AWS_PROFILE=my-account
AWS_REGION=ap-southeast-2
```

#### Multi-Account (Advanced)
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

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup examples.

## Scoring Algorithm

The scoring algorithm ranks users based on multiple factors:

### 1. Level Weights
How much each skill hierarchy level contributes to the score:
- **L1 (Categories)**: 0.1 - Very broad, minimal weight
- **L2 (Sub-categories)**: 0.2 - Broader context
- **L3 (Generic Skills)**: 0.5 - **MOST IMPORTANT** - Core competencies
- **L4 (Technologies)**: 0.3 - Specific tools/tech

### 2. Rating Multipliers (Exponential)
User's self-assessed proficiency level:
- **Beginner (1)**: 1.0x
- **Intermediate (2)**: 2.0x
- **Advanced (3)**: 4.0x

Rationale: Advanced users with relevant L3 skills should rank higher than Intermediate users even if the latter have more specific L4 tool matches.

### 3. Similarity Score
From vector search (0-1 scale):
- Derived from cosine distance: `similarity = 1 - distance`
- Measures how semantically close the skill is to the query

### 4. Transfer Bonus
Partial credit for related technology experience:
- If query matches an L3 skill, but user only has the L4 technology under a **different** L3, they get partial credit
- **Example**: 
  - Query matches: "Serverless Architecture (L3) > AWS (L4)"
  - User has: "Cloud Security (L3) > AWS (L4)"
  - → User gets transfer bonus for AWS competence
- **Bonus**: 0.02 per transferable technology, capped at 0.15 (15%)

### Formula

For each matched skill:
```
base_score = similarity × level_weight × rating_multiplier
```

User total score:
```
raw_score = Σ(base_score for all matched skills) + transfer_bonus
normalized_score = (raw_score / max_possible_score) × 100
```

### Ranking Example

Query: "Container Orchestration (L3) + Kubernetes (L4)"

1. **User C**: Has Kubernetes (L4) under Container Orchestration (L3)
   - Direct L3 + L4 match = **HIGHEST** score

2. **User B**: Has Docker (L4) under Container Orchestration (L3)
   - Direct L3 match + different L4 = **HIGH** score

3. **User A**: Has Kubernetes (L4) under DevOps (different L3)
   - No L3 match, but gets transfer bonus = **MEDIUM** score
   - Ranks above users with NO relevant skills

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- AWS CLI configured with at least one profile
- Access to required AWS services:
  - **AWS Bedrock** (for embeddings) - typically in `us-east-1`
  - **AWS S3 Vectors** (for vector index) - any region
  - **S3 bucket** with user data (`skills-selector-*`)

### Setup and Run

The `setup.sh` script handles everything:

```bash
cd skill-search
./setup.sh
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

### Access the Application

After setup completes:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Testing

```bash
# Quick API validation
./test_api.sh

# Comprehensive tests
python test_api.py
```

### Monitoring

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

## Manual Setup (Advanced)

> **Note**: For most users, `./setup.sh` is recommended. Manual setup is for advanced scenarios or development.

### Backend Development Setup

```bash
cd skill-search/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create and configure .env file
cp .env.example .env
# Edit .env with your AWS configuration (see Configuration section)

# Ingest user data (uses INGESTION_AWS_PROFILE from .env)
python scripts/ingest_users.py

# Override profile if needed
python scripts/ingest_users.py --profile your-profile

# Run backend locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development Setup

```bash
cd skill-search/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will automatically proxy API requests to `http://localhost:8000`.

## Project Structure

```
skill-search/
├── backend/
│   ├── api/
│   │   ├── models.py          # Pydantic models
│   │   └── routes.py          # REST endpoints
│   ├── services/
│   │   ├── user_repository.py # Data access layer
│   │   ├── vector_search.py   # Vector search service
│   │   └── scoring.py         # Scoring algorithm
│   ├── scripts/
│   │   ├── ingest_users.py    # S3 → user_db.json
│   │   └── validate_aws.py    # AWS validation
│   ├── data/
│   │   └── user_db.json       # User database (generated)
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI app
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   └── Dockerfile             # Backend container
├── frontend/
│   ├── public/
│   │   └── index.html         # HTML template
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchPage.js  # Main search interface
│   │   │   ├── SearchBar.js   # Search input
│   │   │   ├── SkillResults.js # Matched skills display
│   │   │   ├── UserResults.js  # User cards
│   │   │   ├── ScoreBuckets.js # Expandable buckets
│   │   │   └── UserDetail.js   # User detail page
│   │   ├── styles/
│   │   │   └── main.css       # Application styles
│   │   ├── App.js             # Main app component
│   │   └── index.js           # React entry point
│   ├── package.json           # Node dependencies
│   └── Dockerfile             # Frontend container
├── docker-compose.yml         # Multi-container setup
├── setup.sh                   # One-click setup script
└── README.md                  # This file
```

## Configuration

The application uses environment variables in `backend/.env`. The `setup.sh` script creates this file automatically, but you can customize it for advanced scenarios.

### Task-Based AWS Configuration

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
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIM=1024

# =============================================================================
# Task 2: Vector Index Querying (AWS S3 Vectors)
# Override only if vector index is in a different account
# =============================================================================
VECTOR_AWS_PROFILE=profileB
VECTOR_AWS_REGION=ap-southeast-2
VECTOR_BUCKET=skills-vectors-1760131105
VECTOR_INDEX=skills-index

# =============================================================================
# Task 3: Data Ingestion (AWS S3 Read)
# Override only if S3 data bucket is in a different account
# =============================================================================
INGESTION_AWS_PROFILE=profileC
INGESTION_AWS_REGION=ap-southeast-2
INGESTION_BUCKET=skills-selector-1760061975
```

**For Single Account**: Just set `AWS_PROFILE` and `AWS_REGION`. Comment out or remove task-specific overrides.

**For Multi-Account**: Set task-specific profiles as shown above.

See [CONFIGURATION.md](CONFIGURATION.md) for detailed examples and migration guide.

### Scoring Configuration
```bash
# Level weights
LEVEL_WEIGHT_L1=0.1
LEVEL_WEIGHT_L2=0.2
LEVEL_WEIGHT_L3=0.5
LEVEL_WEIGHT_L4=0.3

# Rating multipliers
RATING_MULTIPLIER_1=1.0
RATING_MULTIPLIER_2=2.0
RATING_MULTIPLIER_3=4.0

# Transfer bonus
TRANSFER_BONUS_PER_TECH=0.02
TRANSFER_BONUS_CAP=0.15

# Score buckets
EXCELLENT_MIN_SCORE=80
STRONG_MIN_SCORE=60
GOOD_MIN_SCORE=40
```

### Display Configuration
```bash
TOP_USERS_COUNT=5
USERS_PER_PAGE=10
```

## API Endpoints

### Search Users
```http
POST /api/search
Content-Type: application/json

{
  "query": "AWS Lambda and serverless architecture",
  "top_k_skills": 10,
  "top_n_users": 5
}
```

**Response**: Matched skills, top users, and score buckets

### Get User Detail
```http
GET /api/users/{email}
```

**Response**: User details with full skill breakdown

### Health Check
```http
GET /api/health
```

**Response**: Service status and user count

### Statistics
```http
GET /api/stats
```

**Response**: Application statistics and configuration

## Troubleshooting

### Quick Diagnostics

```bash
# Check if containers are running
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Test backend API
./test_api.sh

# Check vector index accessibility
cd backend
python scripts/check_vector_index.py
```

### AWS Configuration Issues

```bash
# Verify AWS profile exists
aws configure list-profiles

# Test credentials (replace 'your-profile' with your actual profile name)
aws sts get-caller-identity --profile your-profile

# Check which profiles the app is using
docker-compose logs backend | grep "AWS"
```

**Common Issues:**
- **Wrong region**: Vector bucket must be in correct region (check `.env`)
- **Missing permissions**: Ensure profile has Bedrock, S3 Vectors, and S3 access
- **Profile not found**: Check `~/.aws/credentials` file

### User Data Ingestion Issues

```bash
# Manual ingestion with specific bucket
cd backend
python scripts/ingest_users.py --bucket skills-selector-1760061975

# Check what buckets are available
aws s3 ls --profile your-profile

# Verify user_db.json was created
ls -lh backend/data/user_db.json
```

### Port Conflicts

If ports 3000 or 8000 are already in use, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change host port (left side)
  frontend:
    ports:
      - "3001:3000"  # Change host port (left side)
```

Then access at `http://localhost:3001` and `http://localhost:8001`.

### Container Issues

```bash
# Complete reset
docker-compose down
docker-compose up -d --build

# Nuclear option - clean everything
docker-compose down -v
docker system prune -a
./setup.sh
```

### Search Not Working

1. **Check backend logs**:
   ```bash
   docker-compose logs backend | grep -i error
   ```

2. **Verify vector index**:
   ```bash
   cd backend
   python scripts/check_vector_index.py
   ```

3. **Test API directly**:
   ```bash
   curl -X POST http://localhost:8000/api/search \
     -H "Content-Type: application/json" \
     -d '{"query": "Python programming", "top_k_skills": 5}'
   ```

4. **Check configuration**:
   - Verify `VECTOR_BUCKET` and `VECTOR_INDEX` in `.env`
   - Ensure `VECTOR_AWS_REGION` matches where bucket exists
   - Check `EMBEDDING_AWS_REGION` for Bedrock access

### Frontend Issues

```bash
# Check frontend logs
docker-compose logs frontend | grep -i error

# Verify frontend is running
curl -I http://localhost:3000

# Check if it can reach backend
docker-compose exec frontend curl http://backend:8000/api/health
```

### Getting Help

1. Check backend startup logs:
   ```bash
   docker-compose logs backend --tail=20
   ```

2. Look for configuration summary:
   ```
   AWS Default Profile: default
   AWS Default Region: ap-southeast-2
     → Embedding (Bedrock): profileA / us-east-1
     → Vector Search: profileB / ap-southeast-2
     → Data Ingestion: profileC / ap-southeast-2
   ```

3. Run diagnostics:
   ```bash
   ./test_api.sh
   cd backend && python scripts/check_vector_index.py
   ```
