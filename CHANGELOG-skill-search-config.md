# Skill Search Configuration Externalization

## Summary
Removed all hardcoded AWS profiles and bucket names from the Skill Search component, implementing an interactive setup script similar to the Skill Embeddings component.

## Changes Made

### 1. Setup Script (`skill-search-setup.sh`)
**Complete rewrite** with the following features:
- **Interactive AWS Profile Discovery**: Automatically discovers available AWS profiles
- **Service-Specific Profile Selection**: Prompts for 3 different profiles:
  - Bedrock profile (for embedding generation via Bedrock API)
  - S3 Vectors profile (for querying vector indexes)
  - S3 profile (for user data ingestion)
- **Bucket Discovery & Selection**:
  - Lists available S3 Vector buckets in the selected region
  - Lists available S3 standard buckets matching 'skills-selector*' pattern
  - Interactive selection with numbered menu
- **.env File Generation**: Auto-generates `backend/.env` with:
  - Selected AWS profiles and regions
  - Selected bucket names
  - Comprehensive comments explaining each setting
  - All scoring and display configuration defaults
- **Optional Data Ingestion**: Offers to run user data ingestion after configuration
- **Optional Docker Startup**: Offers to start Docker containers after setup
- **Clear Output**: Uses shared logging utilities for consistent messaging
- **Proper I/O Handling**: All prompts use `/dev/tty` redirection, lists output to stderr

### 2. Backend Configuration (`backend/config.py`)
- **Removed hardcoded buckets**:
  - `vector_bucket`: Changed from `"skills-vectors-1760131105"` to `Field(default="", description="...")`
  - `ingestion_bucket`: Changed from `"skills-selector-1760061975"` to `Field(default="", description="...")`
- **Added Pydantic Field imports**: Import `Field` from `pydantic` for better field documentation
- **Enhanced documentation**: Added descriptive help text for bucket configuration fields
- **Fixed Pydantic validation**: Added `extra='ignore'` to SettingsConfigDict to allow .env variables that aren't explicitly defined in the Settings class (forward compatibility)

### 3. Environment Template (`backend/.env.example`)
**Complete rewrite** to match skill-embeddings pattern:
- **Comprehensive header**: Explains setup options and configuration sections
- **Placeholder values**: Uses `<your-aws-profile>`, `<your-vector-bucket-name>`, etc.
- **Clear comments**: Each setting includes:
  - Purpose description
  - When it's used
  - Example format
  - How to provision (e.g., "Created via: Skill Embeddings > Provision")
- **Removed old/unused fields**: Cleaned up obsolete configuration variables
- **Aligned with config.py**: Environment variables match new Settings class structure

### 4. Documentation Updates

#### README.md
- **Updated configuration examples**: Replaced hardcoded bucket names with placeholders
- **Added setup script reference**: Recommends using interactive setup script
- **Simplified scoring configuration**: Removed old complex scoring parameters, kept only active ones
- **Fixed troubleshooting section**: Updated ingestion commands to reflect new config approach

#### docs/skill-search-configuration.md
- **Added setup methods section**: Documents both interactive and manual setup
- **Updated bucket configuration**: Shows placeholders instead of hardcoded values
- **Enhanced notes**: Explains where buckets come from and how to provision them
- **Aligned with new variable names**: Updated all environment variable references

### 5. Git Ignore Verification
Confirmed that sensitive files are properly excluded:
- `.env` files (via pattern on line 45)
- `skill-search/backend/data/user_db.json` (line 52)
- `skill-embeddings/skill-embeddings-config.json` (line 51)

## Files Modified
1. `skill-search/skill-search-setup.sh` - Complete rewrite (620 lines)
2. `skill-search/backend/config.py` - Removed hardcoded bucket defaults
3. `skill-search/backend/.env.example` - Complete rewrite with placeholders
4. `skill-search/README.md` - Updated configuration examples and documentation
5. `skill-search/docs/skill-search-configuration.md` - Updated setup instructions

## Security Improvements
✅ No hardcoded AWS profiles in git-tracked files  
✅ No hardcoded bucket names in git-tracked files  
✅ All sensitive configuration in gitignored files  
✅ Interactive setup prevents accidental commits of credentials  

## Verification Commands
```bash
# Verify no hardcoded buckets in git-tracked files
git ls-files | xargs grep -l "skills-selector-1760061975\|skills-vectors-1760131105" 2>/dev/null | grep -v ".env" | grep -v "user_db.json"
# Expected: No results

# Verify no hardcoded profiles in skill-search
git ls-files skill-search/ | xargs grep -l "\btroy\b\|\bexalm\b" 2>/dev/null
# Expected: No results

# Verify sensitive files are gitignored
git check-ignore -v skill-search/backend/.env skill-search/backend/data/user_db.json
# Expected: Shows .gitignore rules matching these files
```

## Usage
From the main project menu:
1. Select "Skill Search"
2. Follow interactive prompts to:
   - Select AWS profiles for Bedrock, S3 Vectors, and S3
   - Select vector bucket (from Skill Embeddings)
   - Select ingestion bucket (from Skill Selector)
3. Optionally ingest data and start Docker containers

Or run directly:
```bash
cd skill-search
./skill-search-setup.sh
```

## Implementation Pattern
This implementation follows the **same pattern as Skill Embeddings**:
- Interactive profile discovery
- Bucket listing and selection
- Config file generation with comprehensive comments
- Optional execution steps
- Proper error handling and user feedback

## Next Steps
The project is now ready to be shared without exposing any:
- AWS account identifiers (in bucket names)
- AWS profile names
- Region-specific settings
- Account-specific resource names

Each user will configure their own profiles and buckets through the interactive setup scripts.
