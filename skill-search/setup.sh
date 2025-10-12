#!/bin/bash
#
# Skills Search - One-Click Setup Script
#
# This script sets up and starts the Skills Search application using Docker.
# It handles:
# - Environment configuration
# - AWS validation
# - User data ingestion
# - Docker container startup
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Skills Search - Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed${NC}"
    echo "Please install docker-compose"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo ""

# Check if .env exists, create from example if not
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    if [ -f "backend/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✓ Created backend/.env${NC}"
        echo "Please review and customize backend/.env if needed"
        echo ""
    else
        echo -e "${RED}✗ No .env.example found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo ""
fi

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# List available AWS profiles
echo "Checking AWS profiles..."
echo ""
echo -e "${BLUE}Available AWS Profiles:${NC}"
if [ -f ~/.aws/credentials ]; then
    # Extract profile names from credentials file
    profiles=$(grep '^\[' ~/.aws/credentials | sed 's/\[\(.*\)\]/\1/' | sort)
    if [ -z "$profiles" ]; then
        echo -e "${RED}✗ No AWS profiles found${NC}"
        echo "Please configure AWS: aws configure"
        exit 1
    fi
    
    # Display profiles with numbers
    profile_array=()
    i=1
    while IFS= read -r profile; do
        profile_array+=("$profile")
        echo "  $i) $profile"
        i=$((i + 1))
    done <<< "$profiles"
    
    echo ""
    echo -e "Select AWS profile to use (enter number or name) [default: default]: "
    read -r profile_input
    
    # Handle input
    if [ -z "$profile_input" ]; then
        AWS_PROFILE="default"
    elif [[ "$profile_input" =~ ^[0-9]+$ ]]; then
        # Numeric selection
        index=$((profile_input - 1))
        if [ $index -ge 0 ] && [ $index -lt ${#profile_array[@]} ]; then
            AWS_PROFILE="${profile_array[$index]}"
        else
            echo -e "${RED}✗ Invalid selection${NC}"
            exit 1
        fi
    else
        # Direct profile name
        AWS_PROFILE="$profile_input"
    fi
else
    echo -e "${RED}✗ No AWS credentials file found${NC}"
    echo "Please configure AWS: aws configure"
    exit 1
fi

echo ""
echo -e "${BLUE}Using AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
echo ""

# Validate AWS credentials
echo "Validating AWS credentials..."
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not valid for profile '$AWS_PROFILE'${NC}"
    echo "Please run: aws configure --profile $AWS_PROFILE"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"
echo ""

# Check if user_db.json exists
if [ ! -f "backend/data/user_db.json" ]; then
    echo -e "${YELLOW}⚠ No user database found${NC}"
    echo "Would you like to ingest user data from S3? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Building backend container for ingestion..."
        docker-compose build backend
        
        echo "Running ingestion script..."
        docker-compose run --rm backend python scripts/ingest_users.py --profile "$AWS_PROFILE"
        
        if [ -f "backend/data/user_db.json" ]; then
            echo -e "${GREEN}✓ User data ingested successfully${NC}"
        else
            echo -e "${RED}✗ Ingestion failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Cannot start without user data${NC}"
        echo "Please run ingestion manually:"
        echo "  docker-compose run --rm backend python scripts/ingest_users.py"
        exit 1
    fi
else
    echo -e "${GREEN}✓ User database exists${NC}"
    
    # Ask if user wants to re-ingest
    echo ""
    echo "Would you like to re-ingest user data from S3? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Running ingestion script..."
        docker-compose build backend
        docker-compose run --rm backend python scripts/ingest_users.py --profile "$AWS_PROFILE"
        echo -e "${GREEN}✓ User data re-ingested${NC}"
    fi
fi

echo ""
echo "Copying shared styles to frontend..."
# Copy shared styles from parent directory into frontend
if [ -f "../shared/styles.css" ]; then
    mkdir -p frontend/src/styles
    cp ../shared/styles.css frontend/src/styles/shared.css
    echo -e "${GREEN}✓ Shared styles copied${NC}"
else
    echo -e "${RED}✗ Shared styles not found at ../shared/styles.css${NC}"
    exit 1
fi

echo ""
echo "Building containers..."
docker-compose build

echo ""
echo "Starting containers..."
docker-compose up -d

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Skills Search is ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
