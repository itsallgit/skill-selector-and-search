#!/bin/bash
################################################################################
# Skills Search - Setup & Configuration
# ==============================================================================
# Interactive setup script for configuring AWS profiles and buckets
# for the Skills Search application.
#
# This script:
#   1. Discovers available AWS profiles
#   2. Prompts user to select profiles for different services:
#      - Bedrock (embedding generation)
#      - S3 Vectors (vector index querying)
#      - S3 (data ingestion)
#   3. Lists and prompts for S3 Vector bucket selection
#   4. Lists and prompts for S3 bucket selection (for user data)
#   5. Generates .env file with configuration
#   6. Optionally ingests user data
#   7. Starts Docker containers
#
# Usage:
#   ./skill-search-setup.sh
################################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source shared utilities
source "${SCRIPT_DIR}/../shared/script-utils/logging.sh"
source "${SCRIPT_DIR}/../shared/script-utils/ui-prompts.sh"

# Colors
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"

################################################################################
# Get Available AWS Profiles
################################################################################
get_aws_profiles() {
    local profiles=()
    
    # Try to get profiles from AWS CLI
    if command -v aws &> /dev/null; then
        while IFS= read -r profile; do
            [ -n "$profile" ] && profiles+=("$profile")
        done < <(aws configure list-profiles 2>/dev/null)
    fi
    
    # If no profiles found, check credentials file manually
    if [ ${#profiles[@]} -eq 0 ] && [ -f ~/.aws/credentials ]; then
        while IFS= read -r line; do
            if [[ "$line" =~ ^\[(.+)\]$ ]]; then
                profiles+=("${BASH_REMATCH[1]}")
            fi
        done < ~/.aws/credentials
    fi
    
    # Return profiles (one per line)
    for profile in "${profiles[@]}"; do
        echo "$profile"
    done
}

################################################################################
# Get Region for Profile
################################################################################
get_profile_region() {
    local profile="$1"
    local region=""
    
    # Try to get region from AWS CLI config
    region=$(aws configure get region --profile "$profile" 2>/dev/null || echo "")
    
    # Default to us-east-1 if not found
    if [ -z "$region" ]; then
        region="us-east-1"
    fi
    
    echo "$region"
}

################################################################################
# Select AWS Profile
################################################################################
select_profile() {
    local purpose="$1"  # Service description
    local profiles=("$@")
    profiles=("${profiles[@]:1}")  # Remove first element (purpose)
    
    if [ ${#profiles[@]} -eq 0 ]; then
        print_error "No AWS profiles found"
        echo "Please configure AWS profiles using: aws configure --profile <profile-name>"
        exit 1
    fi
    
    # Print to stderr so it doesn't get captured
    echo "" >&2
    print_status "Available AWS Profiles:" >&2
    local index=1
    for profile in "${profiles[@]}"; do
        local region=$(get_profile_region "$profile")
        echo "  [$index] $profile (region: $region)" >&2
        ((index++))
    done
    echo "" >&2
    
    local selection=""
    while true; do
        read -r -p "Select profile for ${purpose} [1-${#profiles[@]}]: " selection </dev/tty
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#profiles[@]}" ]; then
            echo "${profiles[$((selection-1))]}"
            return 0
        else
            print_warning "Invalid selection. Please enter a number between 1 and ${#profiles[@]}" >&2
        fi
    done
}

################################################################################
# List Vector Buckets
################################################################################
list_vector_buckets() {
    local profile="$1"
    local region="$2"
    local buckets=()
    
    print_status "Listing S3 Vector buckets..." >&2
    
    while IFS= read -r bucket; do
        [ -n "$bucket" ] && [ "$bucket" != "None" ] && buckets+=("$bucket")
    done < <(aws s3vectors list-vector-buckets --region "$region" --profile "$profile" --query 'vectorBuckets[].vectorBucketName' --output text 2>/dev/null | tr '\t' '\n')
    
    # Return buckets (one per line)
    for bucket in "${buckets[@]}"; do
        echo "$bucket"
    done
}

################################################################################
# Select Vector Bucket
################################################################################
select_vector_bucket() {
    local profile="$1"
    local region="$2"
    local buckets=()
    
    while IFS= read -r bucket; do
        buckets+=("$bucket")
    done < <(list_vector_buckets "$profile" "$region")
    
    if [ ${#buckets[@]} -eq 0 ]; then
        print_error "No S3 Vector buckets found in region $region"
        echo ""
        echo "Please run 'Provision Vector Bucket & Index' from the Skill Embeddings menu first"
        exit 1
    fi
    
    # Print to stderr so it doesn't get captured
    echo "" >&2
    print_status "Available S3 Vector Buckets:" >&2
    local index=1
    for bucket in "${buckets[@]}"; do
        echo "  [$index] $bucket" >&2
        ((index++))
    done
    echo "" >&2
    
    local selection=""
    while true; do
        read -r -p "Select vector bucket [1-${#buckets[@]}]: " selection </dev/tty
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#buckets[@]}" ]; then
            echo "${buckets[$((selection-1))]}"
            return 0
        else
            print_warning "Invalid selection. Please enter a number between 1 and ${#buckets[@]}" >&2
        fi
    done
}

################################################################################
# List S3 Buckets (for data ingestion)
################################################################################
list_s3_buckets() {
    local profile="$1"
    local pattern="${2:-skills-selector}"
    local buckets=()
    
    print_status "Listing S3 buckets matching pattern '$pattern'..." >&2
    
    while IFS= read -r bucket; do
        if [[ "$bucket" =~ ^${pattern} ]]; then
            buckets+=("$bucket")
        fi
    done < <(aws s3api list-buckets --profile "$profile" --query 'Buckets[].Name' --output text 2>/dev/null | tr '\t' '\n')
    
    # Return buckets (one per line)
    for bucket in "${buckets[@]}"; do
        echo "$bucket"
    done
}

################################################################################
# Select S3 Bucket (for data ingestion)
################################################################################
select_s3_bucket() {
    local profile="$1"
    local buckets=()
    
    while IFS= read -r bucket; do
        buckets+=("$bucket")
    done < <(list_s3_buckets "$profile" "skills-selector")
    
    if [ ${#buckets[@]} -eq 0 ]; then
        print_error "No S3 buckets found matching 'skills-selector*'"
        echo ""
        echo "Please run 'Skill Selector' deployment first from the main menu"
        exit 1
    fi
    
    # Print to stderr so it doesn't get captured
    echo "" >&2
    print_status "Available S3 Buckets (for user data ingestion):" >&2
    local index=1
    for bucket in "${buckets[@]}"; do
        echo "  [$index] $bucket" >&2
        ((index++))
    done
    echo "" >&2
    
    local selection=""
    while true; do
        read -r -p "Select S3 bucket for data ingestion [1-${#buckets[@]}]: " selection </dev/tty
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#buckets[@]}" ]; then
            echo "${buckets[$((selection-1))]}"
            return 0
        else
            print_warning "Invalid selection. Please enter a number between 1 and ${#buckets[@]}" >&2
        fi
    done
}

################################################################################
# Generate .env File
################################################################################
generate_env_file() {
    local bedrock_profile="$1"
    local bedrock_region="$2"
    local vector_profile="$3"
    local vector_region="$4"
    local vector_bucket="$5"
    local ingestion_profile="$6"
    local ingestion_region="$7"
    local ingestion_bucket="$8"
    
    print_status "Generating .env file..."
    
    cat > "${SCRIPT_DIR}/backend/.env" << EOF
################################################################################
# Skills Search Backend - Environment Configuration
# ==============================================================================
# This file is AUTO-GENERATED by skill-search-setup.sh
# DO NOT commit this file to version control
# 
# Configuration includes:
#   - AWS Profile settings for different services
#   - S3 Vector Bucket for embeddings search
#   - S3 Bucket for user data ingestion
#   - Search scoring parameters
#   - Display settings
################################################################################

# AWS Configuration
# ------------------------------------------------------------------------------
# General AWS profile (fallback for services that don't have specific profiles)
AWS_PROFILE=${bedrock_profile}
AWS_REGION=${bedrock_region}

# AWS Bedrock Profile (for generating embeddings via Bedrock API)
# Used when: Generating embeddings for search queries
EMBEDDING_AWS_PROFILE=${bedrock_profile}
EMBEDDING_AWS_REGION=${bedrock_region}

# AWS S3 Vectors Profile (for querying vector indexes)
# Used when: Searching vector embeddings in S3 Vector bucket
VECTOR_AWS_PROFILE=${vector_profile}
VECTOR_AWS_REGION=${vector_region}

# AWS S3 Profile (for ingesting user data)
# Used when: Loading user data from S3 standard bucket
INGESTION_AWS_PROFILE=${ingestion_profile}
INGESTION_AWS_REGION=${ingestion_region}

# S3 Bucket Configuration
# ------------------------------------------------------------------------------
# S3 Vector Bucket (contains skill embeddings and vector index)
VECTOR_BUCKET=${vector_bucket}

# S3 Standard Bucket (contains user data JSON files)
INGESTION_BUCKET=${ingestion_bucket}

# Vector Index Name
VECTOR_INDEX=skills-index

# Embedding Model Configuration
# ------------------------------------------------------------------------------
# Bedrock embedding model to use
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Embedding dimensions
EMBEDDING_DIM=1024

# CORS Configuration
# ------------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Data Paths
# ------------------------------------------------------------------------------
USER_DB_PATH=data/user_db.json

# Search Configuration
# ------------------------------------------------------------------------------
# Number of skills to retrieve from vector search
TOP_K_SKILLS=20

# Minimum similarity threshold
MIN_SIMILARITY=0.35

# Scoring Weights (hierarchy levels)
# ------------------------------------------------------------------------------
LEVEL_WEIGHT_L1=0.1
LEVEL_WEIGHT_L2=0.2
LEVEL_WEIGHT_L3=0.5
LEVEL_WEIGHT_L4=0.3

# Rating Multipliers (exponential)
# ------------------------------------------------------------------------------
RATING_MULTIPLIER_1=1.0
RATING_MULTIPLIER_2=2.0
RATING_MULTIPLIER_3=4.0

# Transfer Bonus
# ------------------------------------------------------------------------------
TRANSFER_BONUS_PER_TECH=0.02
TRANSFER_BONUS_CAP=0.15

# Score Buckets (thresholds)
# ------------------------------------------------------------------------------
EXCELLENT_MIN_SCORE=80
STRONG_MIN_SCORE=60
GOOD_MIN_SCORE=40

# Display Configuration
# ------------------------------------------------------------------------------
TOP_USERS_COUNT=5
USERS_PER_PAGE=10
EOF

    print_success "Created backend/.env with configuration"
}

################################################################################
# Main Setup Flow
################################################################################
main() {
    echo ""
    print_status "=========================================="
    print_status "Skills Search - Interactive Setup"
    print_status "=========================================="
    echo ""
    
    # Step 1: Get available AWS profiles
    print_status "Step 1: Discovering AWS Profiles..."
    local profiles=()
    while IFS= read -r profile; do
        profiles+=("$profile")
    done < <(get_aws_profiles)
    
    if [ ${#profiles[@]} -eq 0 ]; then
        print_error "No AWS profiles found"
        echo "Please configure AWS profiles using: aws configure --profile <profile-name>"
        exit 1
    fi
    
    print_success "Found ${#profiles[@]} AWS profile(s)"
    echo ""
    
    # Step 2: Select AWS profile for Bedrock (embedding generation)
    print_status "Step 2: Configure AWS Bedrock Access"
    echo "  Purpose: Generate embeddings for search queries using Bedrock API"
    echo "  Service: Amazon Bedrock (Titan Embed Text v2 model)"
    local bedrock_profile=$(select_profile "Bedrock (embedding generation)" "${profiles[@]}")
    local bedrock_region=$(get_profile_region "$bedrock_profile")
    print_success "Selected Bedrock profile: $bedrock_profile (region: $bedrock_region)"
    echo ""
    
    # Step 3: Select AWS profile for S3 Vectors (vector search)
    print_status "Step 3: Configure S3 Vectors Access"
    echo "  Purpose: Query vector embeddings index in S3 Vector bucket"
    echo "  Service: Amazon S3 Vectors (for semantic similarity search)"
    local vector_profile=$(select_profile "S3 Vectors (vector index querying)" "${profiles[@]}")
    local vector_region=$(get_profile_region "$vector_profile")
    print_success "Selected S3 Vectors profile: $vector_profile (region: $vector_region)"
    echo ""
    
    # Step 4: Select S3 Vector bucket
    print_status "Step 4: Select S3 Vector Bucket"
    echo "  This bucket should contain the skill embeddings and vector index"
    echo "  (Created via Skill Embeddings > Provision Vector Bucket & Index)"
    local vector_bucket=$(select_vector_bucket "$vector_profile" "$vector_region")
    print_success "Selected vector bucket: $vector_bucket"
    echo ""
    
    # Step 5: Select AWS profile for S3 (data ingestion)
    print_status "Step 5: Configure S3 Access (Data Ingestion)"
    echo "  Purpose: Load user data from S3 standard bucket"
    echo "  Service: Amazon S3 (standard bucket for JSON data files)"
    local ingestion_profile=$(select_profile "S3 (user data ingestion)" "${profiles[@]}")
    local ingestion_region=$(get_profile_region "$ingestion_profile")
    print_success "Selected S3 profile: $ingestion_profile (region: $ingestion_region)"
    echo ""
    
    # Step 6: Select S3 bucket for data ingestion
    print_status "Step 6: Select S3 Bucket (User Data)"
    echo "  This bucket should contain the users-master.json file"
    echo "  (Created via Skill Selector deployment)"
    local ingestion_bucket=$(select_s3_bucket "$ingestion_profile")
    print_success "Selected ingestion bucket: $ingestion_bucket"
    echo ""
    
    # Step 7: Generate .env file
    print_status "Step 7: Generate Configuration"
    generate_env_file "$bedrock_profile" "$bedrock_region" "$vector_profile" "$vector_region" "$vector_bucket" "$ingestion_profile" "$ingestion_region" "$ingestion_bucket"
    echo ""
    
    # Step 8: Ask about data ingestion
    print_status "Step 8: Data Ingestion"
    echo "Would you like to ingest user data now?"
    echo "  This will:"
    echo "    - Download users-master.json from S3 bucket: $ingestion_bucket"
    echo "    - Validate JSON structure"
    echo "    - Store in local database (backend/data/user_db.json)"
    echo ""
    local ingest_choice=""
    read -r -p "Ingest user data now? (y/n) [y]: " ingest_choice </dev/tty
    ingest_choice=${ingest_choice:-y}
    
    if [[ "$ingest_choice" =~ ^[Yy]$ ]]; then
        print_status "Running data ingestion..."
        cd "${SCRIPT_DIR}/backend"
        
        # Check if Python is available
        if ! command -v python3 &> /dev/null; then
            print_error "Python 3 is not installed"
            echo "Please install Python 3 to run data ingestion"
            exit 1
        fi
        
        # Check if virtual environment exists, create if not
        if [ ! -d "venv" ]; then
            print_status "Creating Python virtual environment..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Install requirements if needed
        if [ -f "requirements.txt" ]; then
            print_status "Installing Python dependencies..."
            pip install -q -r requirements.txt
        fi
        
        # Run ingestion script
        print_status "Ingesting users from S3..."
        python3 scripts/ingest_users.py
        
        deactivate
        cd "$SCRIPT_DIR"
        
        print_success "Data ingestion completed"
        echo ""
    else
        print_warning "Skipping data ingestion"
        echo "You can run ingestion later with:"
        echo "  cd backend && python3 scripts/ingest_users.py"
        echo ""
    fi
    
    # Step 9: Start Docker containers
    print_status "Step 9: Start Docker Containers"
    echo ""
    local start_choice=""
    read -r -p "Start Docker containers now? (y/n) [y]: " start_choice </dev/tty
    start_choice=${start_choice:-y}
    
    if [[ "$start_choice" =~ ^[Yy]$ ]]; then
        print_status "Starting Docker containers..."
        docker-compose up -d
        
        print_success "Docker containers started successfully!"
        echo ""
        echo "=========================================="
        echo "Skills Search is now running:"
        echo "  - Backend API:  http://localhost:8000"
        echo "  - Frontend UI:  http://localhost:3000"
        echo "  - API Docs:     http://localhost:8000/docs"
        echo "=========================================="
        echo ""
        echo "To view logs:"
        echo "  docker-compose logs -f"
        echo ""
        echo "To stop:"
        echo "  docker-compose down"
        echo ""
    else
        print_warning "Skipping Docker startup"
        echo "You can start containers later with:"
        echo "  docker-compose up -d"
        echo ""
    fi
    
    print_success "Setup completed successfully!"
}

# Run main function
main
