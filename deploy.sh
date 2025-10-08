#!/bin/bash

# Skills Selector - AWS S3 Deployment Script
# This script creates an S3 bucket, configures it for static website hosting,
# sets up CORS for client-side file operations, and deploys the application.

set -e  # Exit on any error

# Configuration defaults (overridden during prompts)
BUCKET_NAME="skills-selector-$(date +%s)"  # Default auto-generated name for new bucket
REGION="ap-southeast-2"                     # Default region (updated if existing bucket differs)
AWS_PROFILE=""                              # Selected interactively
USING_EXISTING_BUCKET=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_confirm() { echo -e "${RED}[ATTENTION]${NC} $1"; }

# Select AWS CLI profile
select_aws_profile() {
    print_status "Detecting available AWS CLI profiles..."
    # Collect profiles into array (bash 3 compatible)
    profiles=()
    while IFS= read -r p; do
        [ -n "$p" ] && profiles+=("$p")
    done <<EOF
$(aws configure list-profiles 2>/dev/null || true)
EOF

    if [ ${#profiles[@]} -eq 0 ]; then
        print_error "No AWS profiles found. Configure one with: aws configure --profile <name>"
        exit 1
    fi

    echo "Available AWS profiles:";
    for p in "${profiles[@]}"; do
        echo "  - $p"
    done

    while true; do
        read -p "Enter the profile name to use: " input_profile
        if [ -z "$input_profile" ]; then
            print_warning "Profile name cannot be empty."
            continue
        fi
        match_found="false"
        for p in "${profiles[@]}"; do
            if [ "$p" = "$input_profile" ]; then
                match_found="true"
                AWS_PROFILE="$p"
                break
            fi
        done
        if [ "$match_found" = "true" ]; then
            print_success "Selected AWS profile: $AWS_PROFILE"
            break
        else
            print_warning "Profile '$input_profile' not found. Please enter one exactly as listed."
        fi
    done
}

# Check AWS CLI
check_aws_cli() {
    print_status "Checking AWS CLI installation and configuration..."
    if ! command -v aws &>/dev/null; then
        print_error "AWS CLI is not installed. Install it first (brew install awscli / apt / yum)."
        exit 1
    fi
    if [ -z "$AWS_PROFILE" ]; then
        print_error "AWS profile not set (internal script error)."; exit 1; fi
    if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &>/dev/null; then
        print_error "Invalid AWS credentials for profile '$AWS_PROFILE'. Run: aws configure --profile $AWS_PROFILE"; exit 1; fi
    print_success "AWS CLI is properly configured for profile '$AWS_PROFILE'"
}

# Detect region for existing bucket
detect_bucket_region() {
    local bucket="$1"
    local loc
    loc=$(aws s3api get-bucket-location --bucket "$bucket" --profile "$AWS_PROFILE" --query 'LocationConstraint' --output text 2>/dev/null || echo "")
    if [ "$loc" = "None" ] || [ "$loc" = "null" ] || [ -z "$loc" ]; then
        loc="us-east-1"
    fi
    echo "$loc"
}

# Delete existing buckets with skills-selector pattern
delete_existing_buckets() {
    print_status "Checking for existing skills-selector buckets..."
    
    # List all buckets and filter for skills-selector pattern
    existing_buckets=()
    while IFS= read -r bucket; do
        if [[ "$bucket" =~ ^skills-selector ]]; then
            existing_buckets+=("$bucket")
        fi
    done < <(aws s3api list-buckets --profile "$AWS_PROFILE" --query 'Buckets[].Name' --output text 2>/dev/null | tr '\t' '\n')
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        print_status "No existing skills-selector buckets found."
        return
    fi
    
    echo
    print_warning "Found ${#existing_buckets[@]} existing skills-selector bucket(s):"
    for bucket in "${existing_buckets[@]}"; do
        echo "  - $bucket"
    done
    echo
    
    read -p "Do you want to delete any of these buckets? (y/N): " -n 1 -r delete_choice
    echo
    
    if [[ ! $delete_choice =~ ^[Yy]$ ]]; then
        print_status "Skipping bucket deletion."
        return
    fi
    
    # Ask which buckets to delete
    echo "Enter the bucket names to delete (space-separated), or 'all' for all buckets:"
    read -r buckets_to_delete
    
    local delete_list=()
    if [ "$buckets_to_delete" = "all" ]; then
        delete_list=("${existing_buckets[@]}")
    else
        # Split input into array
        read -ra input_buckets <<< "$buckets_to_delete"
        for input_bucket in "${input_buckets[@]}"; do
            # Verify bucket exists in the list
            for existing_bucket in "${existing_buckets[@]}"; do
                if [ "$input_bucket" = "$existing_bucket" ]; then
                    delete_list+=("$input_bucket")
                    break
                fi
            done
        done
    fi
    
    if [ ${#delete_list[@]} -eq 0 ]; then
        print_warning "No valid buckets selected for deletion."
        return
    fi
    
    # Final confirmation
    echo
    print_warning "The following bucket(s) will be PERMANENTLY DELETED with ALL contents:"
    for bucket in "${delete_list[@]}"; do
        echo "  - $bucket"
    done
    echo
    print_confirm "This action CANNOT be undone!"
    read -p "Type 'DELETE' to confirm deletion: " confirmation
    
    if [ "$confirmation" != "DELETE" ]; then
        print_warning "Deletion cancelled."
        return
    fi
    
    # Delete each bucket
    for bucket in "${delete_list[@]}"; do
        print_status "Deleting bucket: $bucket"
        
        # First, remove all objects and versions
        print_status "Removing all objects from $bucket..."
        aws s3 rm "s3://$bucket" --recursive --profile "$AWS_PROFILE" 2>/dev/null || true
        
        # Delete all versions if versioning is enabled
        aws s3api delete-objects --bucket "$bucket" --profile "$AWS_PROFILE" \
            --delete "$(aws s3api list-object-versions --bucket "$bucket" --profile "$AWS_PROFILE" \
            --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null)" 2>/dev/null || true
        
        # Delete all delete markers
        aws s3api delete-objects --bucket "$bucket" --profile "$AWS_PROFILE" \
            --delete "$(aws s3api list-object-versions --bucket "$bucket" --profile "$AWS_PROFILE" \
            --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null)" 2>/dev/null || true
        
        # Finally, delete the bucket itself
        if aws s3api delete-bucket --bucket "$bucket" --profile "$AWS_PROFILE" 2>/dev/null; then
            print_success "Bucket $bucket deleted successfully"
        else
            print_error "Failed to delete bucket $bucket (it may have remaining objects or delete protection)"
        fi
    done
    
    echo
}

# Prompt for existing bucket usage
prompt_existing_bucket() {
    read -p "Deploy to an existing bucket? (y/N): " -n 1 -r existing_choice
    echo
    if [[ $existing_choice =~ ^[Yy]$ ]]; then
        while true; do
            read -p "Enter existing bucket name: " existing_bucket
            existing_bucket="$(echo -n "$existing_bucket" | tr -d '[:space:]')"
            if [ -z "$existing_bucket" ]; then print_warning "Bucket name cannot be empty."; continue; fi
            if aws s3api head-bucket --bucket "$existing_bucket" --profile "$AWS_PROFILE" 2>/dev/null; then
                BUCKET_NAME="$existing_bucket"
                bucket_region=$(detect_bucket_region "$BUCKET_NAME")
                if [ "$REGION" != "$bucket_region" ]; then
                    print_warning "Region mismatch: configured=$REGION, bucket=$bucket_region. Using bucket region."
                    REGION="$bucket_region"
                fi
                USING_EXISTING_BUCKET=1
                print_success "Using existing bucket: $BUCKET_NAME (region: $REGION)"
                break
            else
                print_warning "Bucket '$existing_bucket' not accessible with selected profile. Try again."
            fi
        done
    else
        USING_EXISTING_BUCKET=0
    fi
}

# Create S3 bucket (new bucket path)
create_bucket() {
    print_status "Creating S3 bucket: $BUCKET_NAME"
    if aws s3api head-bucket --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE" 2>/dev/null; then
        print_warning "Bucket $BUCKET_NAME already exists (continuing)."
        return
    fi
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE"
    else
        aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" --profile "$AWS_PROFILE"
    fi
    print_success "Bucket $BUCKET_NAME created successfully"
}

# Function to configure bucket for static website hosting
configure_website_hosting() {
    print_status "Configuring static website hosting..."
    
    # Create website configuration
    cat > website-config.json << EOF
{
    "IndexDocument": {
        "Suffix": "index.html"
    },
    "ErrorDocument": {
        "Key": "index.html"
    }
}
EOF
    
    aws s3api put-bucket-website \
        --bucket $BUCKET_NAME \
        --website-configuration file://website-config.json \
        --profile $AWS_PROFILE
    
    # Clean up temp file
    rm website-config.json
    
    print_success "Static website hosting configured"
}

# Function to set bucket policy for public read access
set_bucket_policy() {
    print_status "Setting bucket policy for public read access..."
    
    # Create bucket policy
    cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        },
        {
            "Sid": "AllowPublicPutObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF
    
    aws s3api put-bucket-policy \
        --bucket $BUCKET_NAME \
        --policy file://bucket-policy.json \
        --profile $AWS_PROFILE
    
    # Clean up temp file
    rm bucket-policy.json
    
    print_success "Bucket policy set for public access"
}

# Function to disable block public access
disable_block_public_access() {
    print_status "Disabling block public access settings..."
    
    aws s3api put-public-access-block \
        --bucket $BUCKET_NAME \
        --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
        --profile $AWS_PROFILE
    
    print_success "Block public access disabled"
}

# Function to configure CORS for client-side file operations
configure_cors() {
    print_status "Configuring CORS for client-side file operations..."
    
    # Create CORS configuration
    cat > cors-config.json << EOF
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
    
    aws s3api put-bucket-cors \
        --bucket $BUCKET_NAME \
        --cors-configuration file://cors-config.json \
        --profile $AWS_PROFILE
    
    # Clean up temp file
    rm cors-config.json
    
    print_success "CORS configuration applied"
}

# Function to update application configuration
update_app_config() {
    print_status "Updating application configuration..."
    
    # Update the bucket name in app.js
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/bucketName: 'deloitte-skills-selector'/bucketName: '$BUCKET_NAME'/g" app.js
        sed -i '' "s/region: 'us-east-1'/region: '$REGION'/g" app.js
    else
        # Linux
        sed -i "s/bucketName: 'deloitte-skills-selector'/bucketName: '$BUCKET_NAME'/g" app.js
        sed -i "s/region: 'us-east-1'/region: '$REGION'/g" app.js
    fi
    
    print_success "Application configuration updated"
}

# Function to deploy files to S3
deploy_files() {
    print_status "Deploying application files to S3..."
    
    # Sync all files to S3 with proper content types
    aws s3 sync . s3://$BUCKET_NAME \
        --profile $AWS_PROFILE \
        --exclude ".*" \
        --exclude "*.sh" \
        --exclude "*.md" \
        --exclude "node_modules/*" \
        --exclude "package*.json" \
        --delete
    
    # Set content types for specific files
    aws s3 cp index.html s3://$BUCKET_NAME/index.html \
        --content-type "text/html" \
        --profile $AWS_PROFILE
    
    aws s3 cp styles.css s3://$BUCKET_NAME/styles.css \
        --content-type "text/css" \
        --profile $AWS_PROFILE
    
    aws s3 cp app.js s3://$BUCKET_NAME/app.js \
        --content-type "application/javascript" \
        --profile $AWS_PROFILE
    
    aws s3 cp skills-master.json s3://$BUCKET_NAME/skills-master.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp skill-levels-mapping.json s3://$BUCKET_NAME/skill-levels-mapping.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp skill-ratings-mapping.json s3://$BUCKET_NAME/skill-ratings-mapping.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp users-master.json s3://$BUCKET_NAME/users-master.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    print_success "Files deployed successfully"
}

# Function to get website URL
get_website_url() {
    local website_url="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
    if [ "$REGION" = "us-east-1" ]; then
        website_url="http://$BUCKET_NAME.s3-website.amazonaws.com"
    fi
    echo $website_url
}

# Main deployment function
main() {
    echo "========================================"; echo "Skills Selector - AWS Deployment"; echo "========================================"; echo
    select_aws_profile
    check_aws_cli
    
    # Check for existing buckets and offer deletion option
    delete_existing_buckets
    
    prompt_existing_bucket

    print_status "Starting deployment with the following configuration:"
    echo "  Bucket Name: $BUCKET_NAME"; [ "$USING_EXISTING_BUCKET" = "1" ] && echo "  (Existing bucket mode)"
    echo "  Region: $REGION"; echo "  AWS Profile: $AWS_PROFILE"; echo

    read -p "Proceed with deployment? (y/N): " -n 1 -r; echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then print_warning "Deployment cancelled"; exit 0; fi

    if [ "$USING_EXISTING_BUCKET" = "0" ]; then
        create_bucket
        disable_block_public_access
        set_bucket_policy
        configure_website_hosting
        configure_cors
    else
        print_status "Existing bucket mode: skipping bucket creation & configuration."
    fi

    update_app_config

    if [ "$USING_EXISTING_BUCKET" = "1" ]; then
        print_status "Deploying to existing bucket (preserving users-master.json and /users directory) ..."
        aws s3 sync . s3://$BUCKET_NAME \
            --profile "$AWS_PROFILE" \
            --exclude ".*" \
            --exclude "*.sh" \
            --exclude "*.md" \
            --exclude "node_modules/*" \
            --exclude "package*.json" \
            --exclude "users-master.json" \
            --exclude "users/*" \
            --delete
        aws s3 cp index.html s3://$BUCKET_NAME/index.html --content-type "text/html" --profile "$AWS_PROFILE"
        aws s3 cp styles.css s3://$BUCKET_NAME/styles.css --content-type "text/css" --profile "$AWS_PROFILE"
        aws s3 cp app.js s3://$BUCKET_NAME/app.js --content-type "application/javascript" --profile "$AWS_PROFILE"
        aws s3 cp skills-master.json s3://$BUCKET_NAME/skills-master.json --content-type "application/json" --profile "$AWS_PROFILE"
        aws s3 cp skill-levels-mapping.json s3://$BUCKET_NAME/skill-levels-mapping.json --content-type "application/json" --profile "$AWS_PROFILE" || true
        aws s3 cp skill-ratings-mapping.json s3://$BUCKET_NAME/skill-ratings-mapping.json --content-type "application/json" --profile "$AWS_PROFILE" || true
        aws s3 cp users.html s3://$BUCKET_NAME/users.html --content-type "text/html" --profile "$AWS_PROFILE" || true
        print_success "Files deployed (users-master.json and /users directory preserved)"
    else
        deploy_files
    fi
    
    echo
    echo "========================================"; print_success "Deployment completed successfully!"; echo "========================================"; echo
    echo "Open the application in your browser:"; echo -e "${GREEN}$(get_website_url)${NC}"; echo
    print_warning "Security Note: Public access enabled. Review bucket policy before production use."; echo
}

# Run main function
main "$@"