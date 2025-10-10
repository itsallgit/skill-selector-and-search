# Skills Selector & Search Platform

This project has two integrated capabilities:

1. **Skills Selector** - Web application for interactive skill selection and management
2. **Skills Search** - Semantic search backend for finding users by skill expertise

> Please note: This is POC project that has deprioritised platform hardening and security in the interest of demonstrating value.

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Features](#features)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Skills Selector Application](#skills-selector-application)
- [Skills Search Backend](#skills-search-backend)
- [Data Management](#data-management)
- [Architecture](#architecture)
- [Development](#development)
- [Security Considerations](#security-considerations)

## Repository Structure

```
skill-selector/                 # Web application (deployed to S3)
├── index.html                  # Main skill explorer interface
├── users.html                  # User listing and skill counts
├── styles.css                  # Application styles
└── app.js                      # Core application logic

skill-search/                   # Semantic search backend (not deployed to S3)
└── scripts/
    ├── skill-embeddings.py     # Generate and upload skill vector embeddings
    └── user-skills-search.py   # Semantic search implementation (TBD)

data/                           # JSON data files (deployed to S3)
├── skills-master.json          # Hierarchical skills database
├── skill-levels-mapping.json   # Level number to semantic name mapping
├── skill-ratings-mapping.json  # Skill proficiency level definitions
├── users-master.json           # User registry and references
└── skill-embeddings.jsonl      # Generated skill embeddings cache (local only)

scripts/                        # Shared deployment utilities
├── config.sh                   # Configuration and constants
├── logging.sh                  # Colored output utilities
├── ui-prompts.sh               # User interaction prompts
├── aws-auth.sh                 # AWS authentication and region detection
└── bucket-operations.sh        # S3 bucket management operations

docs/                           # Documentation

deploy-skill-selector.sh        # Skills Selector application deployment
deploy-skill-search.sh          # Skills Search infrastructure deployment
README.md                       # This file
```

## Application Structure

### Skill Hierarchy
- **Level 1 (L1)**: Primary skill categories (e.g., Technology, Business Process Consulting)
- **Level 2 (L2)**: Sub-categories within each primary area (e.g., Digital Strategy, Cloud Solutions)
- **Level 3 (L3)**: Generic skills (e.g., Digital Transformation Planning, Cloud Migration Strategy)
- **Level 4 (L4)**: Technologies (e.g., AWS, Azure, Python, TensorFlow)

### Skill ID Generation Algorithm

All skills in the system use **deterministic, collision-resistant IDs** that are:
- **Case-insensitive** but stored in **UPPERCASE** for visual consistency
- **Short and human-readable**: Format `L{level}{6-char-hash}` (e.g., `L1A3F2E9`)
- **Unique**: Based on the full hierarchical path to prevent duplicates
- **Reproducible**: Same skill path always generates the same ID

#### Algorithm Details

This has been included for future capabilities if/when skills can be added view the application.

```javascript
/**
 * Generate a deterministic skill ID
 * Format: L{level}{6-char-hash}
 * 
 * @param {number} level - Skill level (1-4)
 * @param {string} path - Full path (e.g., "Technology > Cloud Solutions > Multi-Cloud Architecture")
 * @returns {string} - Unique ID like "L1A3F2E9"
 */
function generateSkillId(level, path) {
    // 1. Create SHA-256 hash from the full skill path (case-insensitive)
    const hash = crypto
        .createHash('sha256')
        .update(path.toLowerCase().trim())
        .digest('hex');
    
    // 2. Convert first 6 bytes to uppercase alphanumeric characters
    // Using charset: 0-9, A-Z (excluding I, O for clarity)
    const chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ';
    let shortHash = '';
    
    for (let i = 0; i < 6; i++) {
        const byte = parseInt(hash.substr(i * 2, 2), 16);
        shortHash += chars[byte % chars.length];
    }
    
    // 3. Return formatted ID: L{level}{hash}
    return `L${level}${shortHash}`;
}
```

#### ID Examples
- `L1VX34BJ` - Level 1: Technology
- `L2B5980F` - Level 2: Technology > Cloud Solutions
- `L387LN3G` - Level 3: Technology > Cloud Solutions > Multi-Cloud Architecture
- `L4ALNXVK` - Level 4: Technology > Cloud Solutions > Multi-Cloud Architecture > Kubernetes

#### Why This Algorithm?

- **No Duplicates**: Hash-based approach ensures different paths get different IDs
- **Stable**: Same skill path always produces the same ID (deterministic)
- **Collision-Resistant**: SHA-256 provides excellent distribution
- **Human-Readable**: Short alphanumeric format is easier to read than full UUIDs
- **Hierarchical**: Level prefix provides quick visual identification
- **Case-Insensitive**: Path is normalized before hashing for consistency

## Getting Started

### Prerequisites

1. **AWS CLI v2.15.0+**: Install and configure the AWS CLI
   ```bash
   # macOS
   brew install awscli
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install awscli
   
   # Windows
   # Download from: https://aws.amazon.com/cli/
   ```

2. **AWS Configuration**: Configure your AWS credentials and profile
   ```bash
   aws configure --profile your-profile-name
   ```
   
   You'll need:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., ap-southeast-2 for Sydney)
   - Output format (json recommended)

3. **S3 Vectors Support** (for semantic search features):
   - Ensure AWS CLI supports `s3vectors` commands
   - Check with: `aws s3vectors list-vector-buckets --region your-region --profile your-profile`

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd skill-selector
   ```

2. **Review the structure**:
   ```bash
   ls -la
   # Should see: skill-selector/, skill-search/, data/, scripts/, docs/, deploy-*.sh, README.md
   ```

3. **Deploy the Skills Selector Application**:
   ```bash
   # Make script executable
   chmod +x deploy-skill-selector.sh
   
   # Run deployment
   ./deploy-skill-selector.sh
   ```

4. **Deploy the Skills Search Infrastructure** (optional):
   ```bash
   # Make script executable
   chmod +x deploy-skill-search.sh
   
   # Run deployment
   ./deploy-skill-search.sh
   ```

5. **Follow the prompts**:
   - Select your AWS profile
   - Choose deployment options (new/existing bucket, delete old buckets, etc.)
   - Get your application URL upon completion

## Deployment

### Deployment Scripts Overview

The project uses two separate deployment scripts with shared utilities:

#### `deploy-skill-selector.sh`
Deploys the Skills Selector web application to AWS S3:

**What it deploys:**
- From `skill-selector/`: Web application files (HTML, CSS, JS)
- From `data/`: JSON data files (skills, users, mappings)
- All files deployed to S3 bucket root (flat structure)

#### `deploy-skill-search.sh`
Provisions infrastructure for Skills Search semantic search:

**What it deploys:**
- AWS S3 Vector buckets for storing skill embeddings
- Infrastructure for vector search operations

#### Shared Utilities (`scripts/`)
Both deployment scripts leverage reusable modules:
- `config.sh` - Centralized configuration
- `logging.sh` - Colored console output
- `ui-prompts.sh` - Interactive user prompts
- `aws-auth.sh` - AWS authentication and region detection
- `bucket-operations.sh` - S3 bucket CRUD operations

**What doesn't get deployed:**
- `skill-search/` directory (Python backend, runs locally)
- `docs/` directory (documentation)
- `scripts/` directory (deployment utilities)
- `.git/` and other development files

## Skills Selector Application

### File Structure (Deployed)

When deployed to S3, files maintain a flat structure:
```
s3://skills-selector-<timestamp>/
├── index.html                  # Main application
├── users.html                  # Users page
├── styles.css                  # Styles
├── app.js                      # Application logic
├── skills-master.json          # Skills database
├── skill-levels-mapping.json   # Level mappings
├── skill-ratings-mapping.json  # Rating definitions
├── users-master.json           # User registry
└── users/                      # User-specific skill files
    ├── user@example.com.json
    └── ...
```

### File Structure (Local Development)

In the repository, files are organized by capability:
```
skill-selector/
├── index.html              # Main application shell
├── users.html              # Users listing page
├── styles.css              # Application styles
└── app.js                  # Core application logic

data/
├── skills-master.json      # Master skills database
├── skill-levels-mapping.json  # Level mappings
├── skill-ratings-mapping.json # Rating definitions
└── users-master.json       # User registry
```

### Usage Guide

#### For End Users

1. **Access Application**: Navigate to the provided S3 website URL
2. **Enter Email**: Provide your email address to create/access your profile
3. **Explore Skills**: Navigate through the three-level skill hierarchy:
   - Click on Level 1 categories to see sub-categories
   - Click on Level 2 sub-categories to see individual skills
   - Click on Level 3 skills to select/deselect them
4. **Review Selections**: View selected skills in the "Selected Skills" section
5. **View Selected**: Use the “View Selected Skills” footer button to jump back up when browsing
6. **Save Progress**: Click "Save Skills" to persist your selections (creates a timestamped JSON in `users/`)
7. **Return Later**: Use the same email to reload your previous selections
8. **Users Overview**: Open Menu → Users to view all registered users and skill counts

### For Administrators

#### Updating Skills

Edit `skills-master.json` to modify the skill database. The file uses a nested array structure:

### Skills Master Data

**File**: `data/skills-master.json`

Four-level hierarchical structure:

```json
[
  {
    "id": "L1VX34BJ",
    "level": 1,
    "title": "Technology",
    "description": "Expertise in technology strategy...",
    "skills": [
      {
        "id": "L2B5980F",
        "level": 2,
        "title": "Cloud Solutions",
        "description": "Cloud platform architecture...",
        "skills": [
          {
            "id": "L387LN3G",
            "level": 3,
            "title": "Multi-Cloud Architecture",
            "description": "Designing solutions across multiple clouds...",
            "skills": [
              {
                "id": "L4ALNXVK",
                "level": 4,
                "title": "Kubernetes",
                "description": "Container orchestration platform"
              }
            ]
          }
        ]
      }
    ]
  }
]
```

### Mapping Files

**skill-levels-mapping.json**: Maps level numbers to semantic names
```json
{
  "1": "L1 Capabilities",
  "2": "L2 Capabilities", 
  "3": "Generic Skills",
  "4": "Technologies"
}
```

**skill-ratings-mapping.json**: Defines proficiency levels
```json
{
  "1": "Beginner",
  "2": "Intermediate",
  "3": "Advanced"
}
```

### User Data

**users-master.json**: Registry of all users
```json
[
  {
    "email": "user@example.com",
    "skillsFile": "users/user@example.com.json",
    "lastUpdated": "2024-10-10T12:34:56Z"
  }
]
```

## Skills Search Backend

### Overview

The Skills Search backend enables semantic search over the skills hierarchy using natural language queries. It uses AWS Bedrock Titan Embeddings V2 to generate vector representations of skills and stores them in AWS S3 Vector Buckets for efficient semantic matching.

### Vector Index Configuration

The semantic search capability uses the following configuration:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Embedding Model** | Amazon Titan Embeddings V2 | AWS-native, cost-effective, optimized for semantic similarity |
| **Embedding Dimension** | 1024 | Balances accuracy with performance; configurable for optimization |
| **Distance Metric** | Cosine Similarity | Standard for text embeddings; normalized and independent of magnitude |
| **Index Name** | `skills-index` | Static name within uniquely-named bucket for consistent references |

**Why Cosine Similarity?**
Cosine similarity is the standard distance metric for text embeddings because:
- It's normalized (independent of vector magnitude)
- It measures the angle between vectors, focusing on direction/meaning rather than scale
- It's the recommended metric for Titan embeddings and most text embedding models
- It better handles semantic similarity regardless of text length

### Embedding Text Format

Skills are embedded using a natural language format that provides hierarchical context for better semantic search results:

**Format**: `"<title> - <description>. This is a <parent_title> <skill_type> within the broader <grandparent_title> domain."`

**Examples:**
- **L1 (Technology)**: 
  ```
  "Technology - Expertise in technology strategy, implementation, and digital transformation initiatives..."
  ```

- **L2 (Digital Strategy)**: 
  ```
  "Digital Strategy - Strategic planning and roadmap development for digital transformation... 
   This is part of Technology."
  ```

- **L3 (Digital Transformation Planning)**: 
  ```
  "Digital Transformation Planning - Developing comprehensive strategies for organizational 
   digital transformation... This is a Digital Strategy skill within the broader Technology domain."
  ```

- **L4 (AWS)**: 
  ```
  "AWS - Amazon Web Services cloud platform. This is a Cloud Solutions technology within the 
   broader Technology domain."
  ```

**Why Natural Language?**
Embedding models are trained on natural language, so sentence-like structures produce better semantic representations than structured formats (like JSON or dot-separated lists). This approach provides context about each skill's position in the hierarchy, improving search accuracy.

### Skill Embeddings Generation

The `skill-embeddings.py` script manages the vector embedding lifecycle:

#### Process Flow

1. **Flatten Skills**: Convert hierarchical skills-master.json to flat structure
2. **Detect Changes**: Compare with cached skill-embeddings.jsonl to find new/modified skills
3. **Generate Embeddings**: Call AWS Bedrock for changed skills only (batch processing)
4. **Save Cache**: Update skill-embeddings.jsonl with all embeddings + metadata
5. **Upload Vectors**: Batch insert all vectors into S3 Vector Index

#### Change Detection

The script maintains a `skill-embeddings.jsonl` file that caches:
- Skill metadata (id, level, title, description, parents)
- Generated embedding text
- Vector embeddings
- Last updated timestamp

Skills are re-embedded only if:
- The skill is new (ID not in cache)
- Title or description has changed
- Parent or ancestor relationships have changed (affects context)

This optimization minimizes AWS Bedrock API calls and costs.

#### Configuration

Key configuration parameters in `skill-embeddings.py`:

> Note: The project currently uses two AWS profiles to handle access to Bedrock and target account for the skill search backend. Eventually this will be consolidated.

```python
# AWS Profiles (can use different accounts/regions)
BEDROCK_PROFILE = "exalm"           # For embedding generation
BEDROCK_REGION = "us-east-1"
S3VECTORS_PROFILE = "exalm"         # For vector storage
S3VECTORS_REGION = "ap-southeast-2"

# Vector Bucket & Index (set by deploy-skill-search.sh)
VECTOR_BUCKET = "skills-vectors-<timestamp>"
VECTOR_INDEX = "skills-index"

# Processing
EMBEDDING_BATCH_SIZE = 25           # Skills per Bedrock API call
MAX_VECTORS_PER_UPLOAD = 50         # Vectors per S3 API call
```

#### Python Environment Setup

The skill embeddings generator requires Python 3.8+ with AWS SDK (boto3). Follow these steps to set up your environment:

##### Prerequisites

- **Python 3.8+**: Check with `python3 --version`
- **pyenv** (recommended): For Python version management
  ```bash
  # Install pyenv (if not already installed)
  brew install pyenv
  
  # Add to your shell profile (~/.bash_profile or ~/.zshrc)
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  ```

##### Setup Steps

1. **Install Python 3.11 (recommended)**
   ```bash
   # Install Python 3.11 via pyenv
   pyenv install 3.11.6
   
   # Set it as the local version for this project
   cd /path/to/skill-selector-and-search
   pyenv local 3.11.6
   
   # Verify
   python3 --version  # Should show Python 3.11.6
   ```

2. **Create a Virtual Environment**
   ```bash
   # Navigate to the skill-search directory
   cd skill-search
   
   # Create virtual environment
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate
   
   # Your prompt should now show (venv)
   ```

3. **Install Dependencies**
   ```bash
   # Install required packages
   pip install -r requirements.txt
   
   # Verify boto3 installation
   python3 -c "import boto3; print(f'boto3 version: {boto3.__version__}')"
   ```

4. **Configure AWS Credentials**
   
   Ensure your AWS profiles are configured in `~/.aws/credentials` and `~/.aws/config`:
   ```ini
   # ~/.aws/credentials
   [exalm]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   
   # ~/.aws/config
   [profile exalm]
   region = us-east-1
   ```

##### Running the Script

```bash
# 1. Deploy vector infrastructure (if not already done)
./deploy-skill-search.sh

# 2. Note the bucket name from deployment output (e.g., skills-vectors-1760131105)

# 3. Update VECTOR_BUCKET in skill-embeddings.py
cd skill-search/scripts
# Edit line 37: VECTOR_BUCKET = "skills-vectors-XXXXXXXXXX"

# 4. Activate virtual environment (if not already active)
cd /path/to/skill-selector-and-search/skill-search
source venv/bin/activate

# 5. Run the embeddings generator
python3 scripts/skill-embeddings.py
```

##### Deactivating the Environment

When you're done working:
```bash
deactivate
```

### Testing Semantic Search

After generating and uploading skill embeddings, you can test the semantic search capability using the interactive test script.

#### test-skill-embeddings.py

The test script demonstrates semantic search by allowing you to query the vector index with natural language and see ranked results based on conceptual similarity.

**Features:**
- Interactive search interface with continuous testing
- Natural language query input or predefined default
- Configurable number of results (top-k)
- Detailed result display with similarity scores
- Qualitative interpretation of match quality
- Full metadata display (skill ID, title, level, ancestors)

**Usage:**

```bash
# Ensure virtual environment is activated
cd skill-search
source venv/bin/activate

# Run the test script
python3 scripts/test-skill-embeddings.py
```

**Interactive Workflow:**

1. **Select Search Option:**
   - Option 1: Use default query (recommended for first test)
   - Option 2: Enter custom query
   - Option 3: Exit

2. **Configure Results:**
   - Specify number of results to return (default: 5)
   - Range: 1-100 results

3. **Review Results:**
   - Each result shows:
     - Skill ID and title
     - Skill level (L1-L4 with description)
     - Similarity score (0-1 scale for cosine similarity)
     - Match quality indicator (🟢 Excellent, 🔵 Strong, 🟡 Good, 🟠 Moderate, ⚪ Weak)
     - Parent and ancestor skill IDs
   - Interpretation section explains the results

4. **Continue Testing:**
   - After each search, choose to search again or exit
   - Test different queries to explore semantic matching

**Default Query:**

The default query is designed to match multiple relevant skills across different hierarchy levels:

```
"We need experienced consultants for a cloud migration project involving 
containerization, microservices architecture, and infrastructure automation 
using Kubernetes and Terraform"
```

**Expected Results:**
- L1: Technology (broad category match)
- L2: Cloud Solutions, DevOps (sub-category matches)
- L3: Cloud Migration Strategy, Container Orchestration, Infrastructure as Code (generic skill matches)
- L4: Kubernetes, Docker, Terraform, AWS, Azure, Google Cloud (specific technology matches)

**Distance & Similarity Score Interpretation:**

> **Important:** AWS S3 Vectors returns **cosine distance** (not similarity). Lower distance = better match.
> - **Distance Formula:** `distance = 1 - similarity`
> - **Conversion:** `similarity = 1 - distance`
> - **Color Progression:** ⚪ White (Weak) → 🟠 Orange → 🟡 Yellow → 🔵 Blue → 🟢 Green (Excellent)

| Distance Range | Similarity Range | Interpretation | Indicator | Meaning |
|----------------|------------------|----------------|-----------|---------|
| 0.00 - 0.15 | 0.85 - 1.00 | Excellent Match | 🟢 | Query terms closely align with skill description and context |
| 0.16 - 0.30 | 0.70 - 0.84 | Strong Match | 🔵 | High semantic relevance with minor differences |
| 0.31 - 0.45 | 0.55 - 0.69 | Good Match | 🟡 | Relevant skill with some semantic distance |
| 0.46 - 0.60 | 0.40 - 0.54 | Moderate Match | 🟠 | Tangentially related or broader conceptual match |
| 0.61+ | 0.00 - 0.39 | Weak Match | ⚪ | Low relevance, may need query refinement |

**Example Output:**

```
Result #1
--------------------------------------------------------------------------------
  Skill ID:      L4ABC123
  Title:         Kubernetes
  Level:         L4 (Technology/Tool)
  Distance:      0.1235 (lower = better match)
  Similarity:    0.8765 🟢 (Excellent Match)
  Parent ID:     L3XYZ456
  Ancestors:     L1VX34BJ, L2ZG2HTE, L3XYZ456

Result #2
--------------------------------------------------------------------------------
  Skill ID:      L3XYZ456
  Title:         Container Orchestration
  Level:         L3 (Generic Skill)
  Distance:      0.1766 (lower = better match)
  Similarity:    0.8234 🔵 (Strong Match)
  Parent ID:     L2ZG2HTE
  Ancestors:     L1VX34BJ, L2ZG2HTE
```

**Testing Tips:**

1. **Start with the Default Query**: Demonstrates multi-level skill matching
2. **Try Specific Technologies**: e.g., "Python machine learning frameworks"
3. **Test Broad Concepts**: e.g., "digital transformation strategy"
4. **Use Industry Terms**: e.g., "financial risk modeling and compliance"
5. **Compare Query Variations**: See how different phrasings affect results
6. **Note Score Patterns**: Higher-level skills (L1, L2) often have lower scores than specific technologies (L4)

**Configuration:**

Key settings in `test-skill-embeddings.py` (should match `skill-embeddings.py`):

```python
# AWS Profiles
BEDROCK_PROFILE = "exalm"           # For embedding generation
S3VECTORS_PROFILE = "troy"          # For vector search
BEDROCK_REGION = "us-east-1"
S3VECTORS_REGION = "ap-southeast-2"

# Vector Bucket & Index
VECTOR_BUCKET = "skills-vectors-<timestamp>"  # Update to match deployment
VECTOR_INDEX = "skills-index"

# Defaults
DEFAULT_TOP_K = 5                   # Number of results to return
```

### Data Files

**skill-embeddings.jsonl** (cached locally, not deployed):
```jsonl
{"_metadata": {"last_updated": "2025-10-10T12:34:56Z", "total_skills": 200, ...}}
{"id": "L1VX34BJ", "level": 1, "title": "Technology", "embedding_text": "...", "vector": [...]}
{"id": "L2ZG2HTE", "level": 2, "title": "Digital Strategy", "embedding_text": "...", "vector": [...]}
...
```

This file serves as both a cache (to avoid re-embedding unchanged skills) and a local backup of all embeddings.

## Architecture

### Technology Stack

**Frontend (Skills Selector)**:
- HTML5 - Semantic markup
- CSS3 - Modern styling (Flexbox, Grid)
- Vanilla JavaScript - No dependencies, ES6+

**Backend (Skills Search)**:
- Python 3.x
- AWS SDK for Python (boto3)
- AWS Bedrock - Titan Embeddings V2 model
- AWS S3 Vectors - Vector storage and semantic search

**Infrastructure**:
- AWS S3 - Static website hosting and object storage
- AWS S3 Vector Buckets - Vector embedding storage and retrieval
- AWS Bedrock - Embedding generation (Titan V2)

### Data Flow

**Skill Selection Flow**:
1. User accesses application via S3 website URL
2. Browser loads HTML/CSS/JS from S3
3. Application fetches `users-master.json` and `skills-master.json`
4. User navigates hierarchy and selects skills
5. Selections saved to `users/<email>.json` via S3 PUT
6. `users-master.json` updated with new file reference

**Vector Generation Flow**:
1. Administrator runs `skill-embeddings.py` script locally
2. Script loads `skills-master.json` and flattens hierarchy
3. Script compares with cached `skill-embeddings.jsonl` to detect changes
4. For new/changed skills, script calls AWS Bedrock Titan V2 to generate embeddings
5. Script saves all embeddings to local `skill-embeddings.jsonl` cache
6. Script uploads all vectors to S3 Vector Index via batch API calls

**Search Flow (TODO)**:

## Development

### Local Development

The Skills Selector application can be tested locally:

```bash
# Serve locally with Python
cd skill-selector
python3 -m http.server 8000

# Open browser
open http://localhost:8000
```

**Note**: Local testing won't persist data to S3. Deploy to AWS for full functionality.

### Modifying Skills

1. **Edit the data file**:
   ```bash
   # Open in your editor
   code data/skills-master.json
   ```

2. **Follow the structure**:
   - Maintain 4-level hierarchy
   - Use deterministic IDs
   - Include all required fields

3. **Test locally** (optional):
   ```bash
   cd skill-selector
   python3 -m http.server 8000
   ```

4. **Deploy changes**:
   ```bash
   ./deploy-skill-selector.sh
   # Use existing bucket to preserve user data
   ```

## Security Considerations

### Current State

⚠️ **Intended for internal/low-sensitivity use**

**Skills Selector Bucket**:
- ✅ Public read access enabled (required for static hosting)
- ✅ CORS configured for client-side operations
- ⚠️ Email addresses stored in plain text
- ⚠️ No authentication required for access
- ⚠️ Anyone can view user skills

**Vector Bucket**:
- ✅ Always encrypted (SSE-S3)
- ✅ Block Public Access enabled
- ✅ IAM-based access control
- ✅ Private by default

### Production Hardening

For production use, consider:

1. **Authentication & Authorization**:
   - Add user authentication (Cognito, OAuth)
   - Implement role-based access control
   - Restrict S3 bucket access to authenticated users

2. **Data Protection**:
   - Encrypt email addresses
   - Implement data retention policies
   - Enable S3 versioning for data recovery

3. **API Layer**:
   - Add API Gateway + Lambda for backend
   - Validate and sanitize all inputs
   - Implement rate limiting

4. **Monitoring**:
   - Enable CloudTrail logging
   - Set up CloudWatch alarms
   - Monitor access patterns

5. **Network**:
   - Use CloudFront for CDN
   - Enable WAF for protection
   - Restrict access by IP/geography if needed
