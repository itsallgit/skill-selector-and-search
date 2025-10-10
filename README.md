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
    ├── skill-embedding.py      # Generate vector embeddings from skills
    └── user-skills-search.py   # Semantic search implementation

data/                           # JSON data files (deployed to S3)
├── skills-master.json          # Hierarchical skills database
├── skill-levels-mapping.json   # Level number to semantic name mapping
├── skill-ratings-mapping.json  # Skill proficiency level definitions
└── users-master.json           # User registry and references

docs/                           # Documentation

deploy.sh                       # Unified deployment script
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
   # Should see: skill-selector/, skill-search/, data/, docs/, deploy.sh, README.md
   ```

3. **Deploy to AWS**:
   ```bash
   # Make script executable
   chmod +x deploy.sh
   
   # Run deployment
   ./deploy.sh
   ```

4. **Follow the prompts**:
   - Select your AWS profile
   - Choose to deploy the Skills Selector application (Y/n)
   - Choose to execute vector bucket flow (Y/n)
   - Get your application URL upon completion

## Deployment

### Deployment Script Overview

The `deploy.sh` script provides a comprehensive deployment workflow:

**What it deploys to S3:**
- From `skill-selector/`: Web application files (HTML, CSS, JS)
- From `data/`: JSON data files (skills, users, mappings)
- All files deployed to S3 bucket root (flat structure)

**What it doesn't deploy:**
- `skill-search/` directory (Python backend, runs locally)
- `docs/` directory (documentation)
- `deploy.sh` itself
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

## Architecture

### Technology Stack

**Frontend (Skills Selector)**:
- HTML5 - Semantic markup
- CSS3 - Modern styling (Flexbox, Grid)
- Vanilla JavaScript - No dependencies, ES6+

**Backend (Skills Search)**:
- Python 3.x
- Vector embedding libraries (TBD)
- AWS SDK for Python (boto3)

**Infrastructure**:
- AWS S3 - Static hosting and object storage
- AWS S3 Vectors - Vector embedding storage

### Data Flow

**Skill Selection Flow**:
1. User accesses application via S3 website URL
2. Browser loads HTML/CSS/JS from S3
3. Application fetches `users-master.json` and `skills-master.json`
4. User navigates hierarchy and selects skills
5. Selections saved to `users/<email>.json` via S3 PUT
6. `users-master.json` updated with new file reference

**Vector Generation (TODO)**:

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
   ./deploy.sh
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
