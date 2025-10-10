#!/bin/bash

# =============================================================================
# Configuration File for Skills Selector & Search Deployment
# =============================================================================
# This file contains all configurable aspects of the deployment scripts.
# Shared by: deploy-skill-selector.sh and deploy-skill-search.sh

# =============================================================================
# AWS CONFIGURATION
# =============================================================================

# Default AWS region (can be overridden by user profile or prompt)
DEFAULT_REGION="ap-southeast-2"

# AWS profile (set during runtime by user selection)
AWS_PROFILE=""

# =============================================================================
# BUCKET CONFIGURATION
# =============================================================================

# Default bucket name patterns (timestamp will be appended)
DEFAULT_BUCKET_NAME_SKILL_SELECTOR="skills-selector-$(date +%s)"
DEFAULT_BUCKET_NAME_SKILL_VECTORS="skills-vectors-$(date +%s)"

# Bucket name prefix patterns for detection and cleanup
BUCKET_PREFIX_SKILL_SELECTOR="skills-selector"
BUCKET_PREFIX_SKILL_VECTORS="skills-vectors"

# =============================================================================
# DEPLOYMENT CONFIGURATION
# =============================================================================

# Skill Selector Application - Source directories
SKILL_SELECTOR_DIR="skill-selector"
DATA_DIR="data"

# Skill Selector Application - Deployment files
SKILL_SELECTOR_FILES=(
    "index.html:text/html"
    "styles.css:text/css"
    "app.js:application/javascript"
    "users.html:text/html"
)

DATA_FILES=(
    "skills-master.json:application/json"
    "skill-levels-mapping.json:application/json"
    "skill-ratings-mapping.json:application/json"
    "users-master.json:application/json"
)

# =============================================================================
# RUNTIME STATE VARIABLES
# =============================================================================

# These variables are set during script execution and shared across functions
BUCKET_NAME_SKILL_SELECTOR=""
BUCKET_NAME_SKILL_VECTORS=""
REGION=""
USING_EXISTING_BUCKET=0

# =============================================================================
# COLOR CODES FOR OUTPUT
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# BUCKET POLICY TEMPLATES
# =============================================================================

# Function to generate bucket policy JSON for public read access
generate_bucket_policy() {
    local bucket_name="$1"
    cat << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${bucket_name}/*"
        },
        {
            "Sid": "AllowPublicPutObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::${bucket_name}/*"
        }
    ]
}
EOF
}

# Function to generate website configuration JSON
generate_website_config() {
    cat << EOF
{
    "IndexDocument": {
        "Suffix": "index.html"
    },
    "ErrorDocument": {
        "Key": "index.html"
    }
}
EOF
}

# Function to generate CORS configuration JSON
generate_cors_config() {
    cat << EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF
}
