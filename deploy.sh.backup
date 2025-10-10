#!/bin/bash

# Skills Selector - AWS S3 Deployment Script
# This script creates an S3 bucket, configures it for static website hosting,
# sets up CORS for client-side file operations, and deploys the application.

set -e  # Exit on any error

# Configuration defaults (overridden during prompts)
BUCKET_NAME_SKILL_SELECTOR="skills-selector-$(date +%s)"  # Default auto-generated name for new bucket
BUCKET_NAME_SKILL_VECTORS="skills-vectors-$(date +%s)"    # Default auto-generated name for vector bucket
REGION="ap-southeast-2"                                    # Default region (updated if existing bucket differs)
AWS_PROFILE=""                                             # Selected interactively
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
            
            # Get region from profile
            get_profile_region
            
            break
        else
            print_warning "Profile '$input_profile' not found. Please enter one exactly as listed."
        fi
    done
}

# Get region from AWS profile
get_profile_region() {
    print_status "Detecting region from AWS profile..."
    
    # Try to get region from profile configuration
    local profile_region
    profile_region=$(aws configure get region --profile "$AWS_PROFILE" 2>/dev/null || echo "")
    
    if [ -n "$profile_region" ]; then
        REGION="$profile_region"
        print_success "Using region from profile: $REGION"
    else
        print_warning "No region configured in profile. Using default: $REGION"
        echo
        read -p "Would you like to use a different region? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter AWS region (e.g., ap-southeast-2, us-east-1): " custom_region
            if [ -n "$custom_region" ]; then
                REGION="$custom_region"
                print_success "Using custom region: $REGION"
            fi
        fi
    fi
}

# Check AWS CLI
check_aws_cli() {
    print_status "Checking AWS CLI installation and configuration..."
    if ! command -v aws &>/dev/null; then
        print_error "AWS CLI is not installed. Install it first (brew install awscli / apt / yum)."
        exit 1
    fi
    
    # Check AWS CLI version
    aws_version=$(aws --version 2>&1)
    print_status "AWS CLI version: $aws_version"
    
    if [ -z "$AWS_PROFILE" ]; then
        print_error "AWS profile not set (internal script error)."; exit 1
    fi
    
    if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &>/dev/null; then
        print_error "Invalid AWS credentials for profile '$AWS_PROFILE'. Run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    print_success "AWS CLI is properly configured for profile '$AWS_PROFILE'"
    
    # Check if s3vectors command is available
    print_status "Checking for s3vectors command availability..."
    if aws s3vectors help &>/dev/null 2>&1; then
        print_success "s3vectors command is available"
    else
        print_warning "s3vectors command not found or not available in this region/account"
        print_warning "S3 Vectors is a preview feature. Ensure:"
        print_warning "  1. Your AWS CLI is up to date (version 2.15.0 or later recommended)"
        print_warning "  2. You have preview access enabled for S3 Vectors"
        print_warning "  3. Your region supports S3 Vectors (check AWS documentation)"
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Deployment cancelled. Please update AWS CLI or enable S3 Vectors preview."
            exit 1
        fi
    fi
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
delete_existing_skill_selector_buckets() {
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

# Delete existing buckets with skills-vectors pattern
delete_existing_skill_vectors_buckets() {
    print_status "Checking for existing skills-vectors buckets in region $REGION..."
    
    # Get the bucket name prefix from BUCKET_NAME_SKILL_VECTORS (extract "skills-vectors")
    local bucket_prefix="${BUCKET_NAME_SKILL_VECTORS%%-*}"
    
    # List all vector buckets and filter for skills-vectors pattern
    existing_buckets=()
    while IFS= read -r bucket; do
        if [[ "$bucket" =~ ^${bucket_prefix}- ]]; then
            existing_buckets+=("$bucket")
        fi
    done < <(aws s3vectors list-vector-buckets --region "$REGION" --profile "$AWS_PROFILE" --query 'vectorBuckets[].vectorBucketName' --output text 2>/dev/null | tr '\t' '\n')
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        print_status "No existing skills-vectors buckets found in region $REGION."
        return
    fi
    
    echo
    print_warning "Found ${#existing_buckets[@]} existing skills-vectors bucket(s):"
    for bucket in "${existing_buckets[@]}"; do
        echo "  - $bucket"
    done
    echo
    
    read -p "Do you want to delete any of these buckets? (y/N): " -n 1 -r delete_choice
    echo
    
    if [[ ! $delete_choice =~ ^[Yy]$ ]]; then
        print_status "Skipping vector bucket deletion."
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
    print_warning "The following vector bucket(s) will be PERMANENTLY DELETED with ALL contents:"
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
        print_status "Deleting vector bucket: $bucket"
        
        # Attempt to delete the vector bucket directly
        # Note: If bucket contains indexes, deletion may fail
        if aws s3vectors delete-vector-bucket --vector-bucket-name "$bucket" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null; then
            print_success "Vector bucket $bucket deleted successfully"
        else
            print_error "Failed to delete vector bucket $bucket (it may contain indexes or have other issues)"
            print_status "If bucket contains indexes, delete them manually first"
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
                BUCKET_NAME_SKILL_SELECTOR="$existing_bucket"
                bucket_region=$(detect_bucket_region "$BUCKET_NAME_SKILL_SELECTOR")
                if [ "$REGION" != "$bucket_region" ]; then
                    print_warning "Region mismatch: configured=$REGION, bucket=$bucket_region. Using bucket region."
                    REGION="$bucket_region"
                fi
                USING_EXISTING_BUCKET=1
                print_success "Using existing bucket: $BUCKET_NAME_SKILL_SELECTOR (region: $REGION)"
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
    local bucket_name="$1"
    local bucket_type="${2:-main}"
    print_status "Creating S3 bucket: $bucket_name (type: $bucket_type)"
    
    if [ "$bucket_type" = "vector" ]; then
        # Check if vector bucket already exists
        print_status "Checking if vector bucket exists..."
        if aws s3vectors get-vector-bucket --vector-bucket-name "$bucket_name" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null; then
            print_warning "Vector bucket $bucket_name already exists (continuing)."
            return
        fi
        
        # Create vector bucket using s3vectors API with explicit region
        print_status "Executing: aws s3vectors create-vector-bucket --vector-bucket-name $bucket_name --region $REGION --profile $AWS_PROFILE"
        if aws s3vectors create-vector-bucket \
            --vector-bucket-name "$bucket_name" \
            --region "$REGION" \
            --profile "$AWS_PROFILE" 2>&1 | tee /tmp/vector-bucket-create.log; then
            print_success "Vector bucket $bucket_name created successfully in region $REGION"
            
            # Verify the bucket was created
            print_status "Verifying vector bucket creation..."
            sleep 2  # Brief wait for eventual consistency
            if aws s3vectors get-vector-bucket --vector-bucket-name "$bucket_name" --region "$REGION" --profile "$AWS_PROFILE" 2>&1; then
                print_success "Vector bucket verified successfully in region $REGION"
            else
                print_error "Vector bucket was reported as created but cannot be found!"
                print_error "It may have been created in a different region. Check AWS Console."
                print_status "Check log file: /tmp/vector-bucket-create.log"
                return 1
            fi
        else
            print_error "Failed to create vector bucket. Check log: /tmp/vector-bucket-create.log"
            return 1
        fi
    else
        # Create general purpose bucket using s3api
        if aws s3api head-bucket --bucket "$bucket_name" --profile "$AWS_PROFILE" 2>/dev/null; then
            print_warning "Bucket $bucket_name already exists (continuing)."
            return
        fi
        if [ "$REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$bucket_name" --profile "$AWS_PROFILE"
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$REGION" \
                --create-bucket-configuration LocationConstraint="$REGION" --profile "$AWS_PROFILE"
        fi
        print_success "Bucket $bucket_name created successfully"
    fi
}

# Function to configure bucket for static website hosting
configure_website_hosting() {
    local bucket_name="$1"
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
        --bucket "$bucket_name" \
        --website-configuration file://website-config.json \
        --profile "$AWS_PROFILE"
    
    # Clean up temp file
    rm website-config.json
    
    print_success "Static website hosting configured"
}

# Function to set bucket policy for public read access
set_bucket_policy() {
    local bucket_name="$1"
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
            "Resource": "arn:aws:s3:::$bucket_name/*"
        },
        {
            "Sid": "AllowPublicPutObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::$bucket_name/*"
        }
    ]
}
EOF
    
    aws s3api put-bucket-policy \
        --bucket "$bucket_name" \
        --policy file://bucket-policy.json \
        --profile "$AWS_PROFILE"
    
    # Clean up temp file
    rm bucket-policy.json
    
    print_success "Bucket policy set for public access"
}

# Function to disable block public access
disable_block_public_access() {
    local bucket_name="$1"
    print_status "Disabling block public access settings..."
    
    aws s3api put-public-access-block \
        --bucket "$bucket_name" \
        --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
        --profile "$AWS_PROFILE"
    
    print_success "Block public access disabled"
}

# Function to configure CORS for client-side file operations
configure_cors() {
    local bucket_name="$1"
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
        --bucket "$bucket_name" \
        --cors-configuration file://cors-config.json \
        --profile "$AWS_PROFILE"
    
    # Clean up temp file
    rm cors-config.json
    
    print_success "CORS configuration applied"
}

# Function to update application configuration
update_app_config() {
    print_status "Updating application configuration..."
    
    # Update the bucket name in app.js (now in skill-selector directory)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/bucketName: 'deloitte-skills-selector'/bucketName: '$BUCKET_NAME_SKILL_SELECTOR'/g" skill-selector/app.js
        sed -i '' "s/region: 'us-east-1'/region: '$REGION'/g" skill-selector/app.js
    else
        # Linux
        sed -i "s/bucketName: 'deloitte-skills-selector'/bucketName: '$BUCKET_NAME_SKILL_SELECTOR'/g" skill-selector/app.js
        sed -i "s/region: 'us-east-1'/region: '$REGION'/g" skill-selector/app.js
    fi
    
    print_success "Application configuration updated"
}

# Function to deploy files to S3
deploy_files() {
    print_status "Deploying application files to S3..."
    
    # Deploy skill-selector web application files
    print_status "Deploying web application files from skill-selector/..."
    
    aws s3 cp skill-selector/index.html s3://$BUCKET_NAME_SKILL_SELECTOR/index.html \
        --content-type "text/html" \
        --profile $AWS_PROFILE
    
    aws s3 cp skill-selector/styles.css s3://$BUCKET_NAME_SKILL_SELECTOR/styles.css \
        --content-type "text/css" \
        --profile $AWS_PROFILE
    
    aws s3 cp skill-selector/app.js s3://$BUCKET_NAME_SKILL_SELECTOR/app.js \
        --content-type "application/javascript" \
        --profile $AWS_PROFILE
    
    aws s3 cp skill-selector/users.html s3://$BUCKET_NAME_SKILL_SELECTOR/users.html \
        --content-type "text/html" \
        --profile $AWS_PROFILE
    
    # Deploy data files from data/
    print_status "Deploying data files from data/..."
    
    aws s3 cp data/skills-master.json s3://$BUCKET_NAME_SKILL_SELECTOR/skills-master.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp data/skill-levels-mapping.json s3://$BUCKET_NAME_SKILL_SELECTOR/skill-levels-mapping.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp data/skill-ratings-mapping.json s3://$BUCKET_NAME_SKILL_SELECTOR/skill-ratings-mapping.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    aws s3 cp data/users-master.json s3://$BUCKET_NAME_SKILL_SELECTOR/users-master.json \
        --content-type "application/json" \
        --profile $AWS_PROFILE
    
    print_success "Files deployed successfully"
}

# Function to get website URL
get_website_url() {
    local bucket_name="$1"
    local website_url="http://$bucket_name.s3-website-$REGION.amazonaws.com"
    if [ "$REGION" = "us-east-1" ]; then
        website_url="http://$bucket_name.s3-website.amazonaws.com"
    fi
    echo $website_url
}

# Function to manage vector bucket workflow
manage_vector_bucket_workflow() {
    echo
    echo "========================================"; echo "Vector Bucket Setup"; echo "========================================"; echo
    print_status "The vector bucket stores embedded skill vectors for semantic search."
    echo
    read -p "Do you want to execute the vector bucket flow? (Y/n): " -n 1 -r execute_flow
    echo
    if [[ $execute_flow =~ ^[Nn]$ ]]; then
        print_warning "Skipping vector bucket workflow."
        return 1
    fi
    
    # List existing vector buckets with skills-vectors pattern
    print_status "Checking for existing skills-vectors buckets in region $REGION..."
    echo
    
    # Get the bucket name prefix from BUCKET_NAME_SKILL_VECTORS (extract "skills-vectors")
    local bucket_prefix="${BUCKET_NAME_SKILL_VECTORS%%-*}"
    
    local existing_buckets=()
    while IFS= read -r bucket; do
        if [[ "$bucket" =~ ^${bucket_prefix}- ]] && [ -n "$bucket" ] && [ "$bucket" != "None" ]; then
            existing_buckets+=("$bucket")
        fi
    done < <(aws s3vectors list-vector-buckets --region "$REGION" --profile "$AWS_PROFILE" --query 'vectorBuckets[].vectorBucketName' --output text 2>/dev/null | tr '\t' '\n')
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        print_status "No existing skills-vectors buckets found in region $REGION."
        echo
    else
        print_status "Found ${#existing_buckets[@]} existing skills-vectors bucket(s):"
        local index=1
        for bucket in "${existing_buckets[@]}"; do
            echo "  [$index] $bucket"
            ((index++))
        done
        echo
        
        # Ask if user wants to delete any buckets
        read -p "Do you want to delete any of these buckets? (y/N): " -n 1 -r delete_choice
        echo
        
        if [[ $delete_choice =~ ^[Yy]$ ]]; then
            echo "Enter 'all' to delete all buckets, or bucket number(s) separated by spaces (e.g., '1 3'):"
            read -r buckets_to_delete
            
            local delete_list=()
            if [ "$buckets_to_delete" = "all" ]; then
                delete_list=("${existing_buckets[@]}")
            else
                # Parse bucket numbers
                read -ra input_numbers <<< "$buckets_to_delete"
                for num in "${input_numbers[@]}"; do
                    if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#existing_buckets[@]}" ]; then
                        delete_list+=("${existing_buckets[$((num-1))]}")
                    fi
                done
            fi
            
            if [ ${#delete_list[@]} -eq 0 ]; then
                print_warning "No valid buckets selected for deletion."
            else
                # Final confirmation
                echo
                print_warning "The following vector bucket(s) will be PERMANENTLY DELETED with ALL contents:"
                for bucket in "${delete_list[@]}"; do
                    echo "  - $bucket"
                done
                echo
                print_confirm "This action CANNOT be undone!"
                read -p "Type 'DELETE' to confirm deletion: " confirmation
                
                if [ "$confirmation" != "DELETE" ]; then
                    print_warning "Deletion cancelled."
                else
                    # Delete each bucket
                    for bucket in "${delete_list[@]}"; do
                        print_status "Deleting vector bucket: $bucket"
                        
                        # Attempt to delete the vector bucket directly
                        # Note: If bucket contains indexes, deletion may fail
                        if aws s3vectors delete-vector-bucket --vector-bucket-name "$bucket" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null; then
                            print_success "Vector bucket $bucket deleted successfully"
                            # Remove from existing_buckets array
                            existing_buckets=("${existing_buckets[@]/$bucket}")
                        else
                            print_error "Failed to delete vector bucket $bucket"
                            print_status "If bucket contains indexes, delete them manually first"
                        fi
                    done
                    echo
                fi
            fi
        fi
    fi
    
    # Ask if user wants to create a new vector bucket
    echo
    read -p "Do you want to create a new vector bucket? (Y/n): " -n 1 -r create_new
    echo
    
    if [[ $create_new =~ ^[Nn]$ ]]; then
        print_warning "Skipping vector bucket creation."
        return 1
    fi
    
    return 0
}

# Function to deploy vector bucket
deploy_vector_bucket() {
    print_status "Starting vector bucket deployment..."
    print_status "Vector Bucket Name: $BUCKET_NAME_SKILL_VECTORS"
    print_status "Region: $REGION"
    print_status "AWS Profile: $AWS_PROFILE"
    echo
    
    # Create vector bucket - note: vector buckets don't need CORS, public access, or website hosting
    # They use a different security model and are always encrypted
    if create_bucket "$BUCKET_NAME_SKILL_VECTORS" "vector"; then
        echo
        print_success "Vector bucket deployment completed!"
        print_status "Note: Vector buckets are always encrypted and have Block Public Access enabled by default."
        print_status "Access control is managed through IAM policies using the 's3vectors' namespace."
        
        # List vector buckets to confirm
        echo
        print_status "Listing all vector buckets in region $REGION to confirm creation..."
        if aws s3vectors list-vector-buckets --region "$REGION" --profile "$AWS_PROFILE" 2>&1; then
            print_success "Vector bucket list retrieved successfully"
        else
            print_error "Failed to list vector buckets. Your bucket may still have been created."
        fi
    else
        print_error "Vector bucket deployment failed!"
        return 1
    fi
}

# Main deployment function
main() {
    echo "========================================"; echo "Skills Selector - AWS Deployment"; echo "========================================"; echo
    select_aws_profile
    check_aws_cli
    
    # Ask if user wants to deploy the main application
    echo
    read -p "Do you want to deploy the Skills Selector application? (Y/n): " -n 1 -r deploy_app
    echo
    
    SKIP_APP_DEPLOYMENT=0
    if [[ $deploy_app =~ ^[Nn]$ ]]; then
        SKIP_APP_DEPLOYMENT=1
        print_status "Skipping Skills Selector application deployment."
        echo
    fi
    
    if [ "$SKIP_APP_DEPLOYMENT" = "0" ]; then
        # Check for existing buckets and offer deletion option
        delete_existing_skill_selector_buckets
        
        prompt_existing_bucket

        print_status "Starting deployment with the following configuration:"
        echo "  Bucket Name: $BUCKET_NAME_SKILL_SELECTOR"; [ "$USING_EXISTING_BUCKET" = "1" ] && echo "  (Existing bucket mode)"
        echo "  Region: $REGION"; echo "  AWS Profile: $AWS_PROFILE"; echo

        read -p "Proceed with deployment? (y/N): " -n 1 -r; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then print_warning "Deployment cancelled"; exit 0; fi

        if [ "$USING_EXISTING_BUCKET" = "0" ]; then
            create_bucket "$BUCKET_NAME_SKILL_SELECTOR" "main"
            disable_block_public_access "$BUCKET_NAME_SKILL_SELECTOR"
            set_bucket_policy "$BUCKET_NAME_SKILL_SELECTOR"
            configure_website_hosting "$BUCKET_NAME_SKILL_SELECTOR"
            configure_cors "$BUCKET_NAME_SKILL_SELECTOR"
        else
            print_status "Existing bucket mode: skipping bucket creation & configuration."
        fi

        update_app_config

        if [ "$USING_EXISTING_BUCKET" = "1" ]; then
            print_status "Deploying to existing bucket (preserving users-master.json and /users directory) ..."
            
            # Deploy web application files from skill-selector/
            aws s3 cp skill-selector/index.html s3://$BUCKET_NAME_SKILL_SELECTOR/index.html --content-type "text/html" --profile "$AWS_PROFILE"
            aws s3 cp skill-selector/styles.css s3://$BUCKET_NAME_SKILL_SELECTOR/styles.css --content-type "text/css" --profile "$AWS_PROFILE"
            aws s3 cp skill-selector/app.js s3://$BUCKET_NAME_SKILL_SELECTOR/app.js --content-type "application/javascript" --profile "$AWS_PROFILE"
            aws s3 cp skill-selector/users.html s3://$BUCKET_NAME_SKILL_SELECTOR/users.html --content-type "text/html" --profile "$AWS_PROFILE" || true
            
            # Deploy data files from data/ (excluding users-master.json to preserve existing)
            aws s3 cp data/skills-master.json s3://$BUCKET_NAME_SKILL_SELECTOR/skills-master.json --content-type "application/json" --profile "$AWS_PROFILE"
            aws s3 cp data/skill-levels-mapping.json s3://$BUCKET_NAME_SKILL_SELECTOR/skill-levels-mapping.json --content-type "application/json" --profile "$AWS_PROFILE" || true
            aws s3 cp data/skill-ratings-mapping.json s3://$BUCKET_NAME_SKILL_SELECTOR/skill-ratings-mapping.json --content-type "application/json" --profile "$AWS_PROFILE" || true
            
            print_success "Files deployed (users-master.json and /users directory preserved)"
        else
            deploy_files
        fi
        
        echo
        echo "========================================"; print_success "Main bucket deployment completed!"; echo "========================================"; echo
        echo "Application URL:"; echo -e "${GREEN}$(get_website_url "$BUCKET_NAME_SKILL_SELECTOR")${NC}"; echo
    fi
    
    # Vector bucket deployment workflow
    if manage_vector_bucket_workflow; then
        # User wants to create a new vector bucket
        echo
        deploy_vector_bucket
        
        echo
        echo "========================================"; print_success "All deployments completed successfully!"; echo "========================================"; echo
        
        if [ "$SKIP_APP_DEPLOYMENT" = "0" ]; then
            echo "Application URL:"; echo -e "${GREEN}$(get_website_url "$BUCKET_NAME_SKILL_SELECTOR")${NC}"; echo
        fi
        
        echo "Vector Bucket Details:"
        echo "  Name: $BUCKET_NAME_SKILL_VECTORS"
        echo "  Region: $REGION"
        echo "  S3 URI: s3://$BUCKET_NAME_SKILL_VECTORS"
        echo
    else
        if [ "$SKIP_APP_DEPLOYMENT" = "0" ]; then
            echo "========================================"; print_success "Deployment completed!"; echo "========================================"; echo
            echo "Application URL:"; echo -e "${GREEN}$(get_website_url "$BUCKET_NAME_SKILL_SELECTOR")${NC}"; echo
        else
            echo "========================================"; print_warning "No deployments were performed."; echo "========================================"; echo
        fi
    fi
    
    if [ "$SKIP_APP_DEPLOYMENT" = "0" ]; then
        print_warning "Security Note: Public access enabled. Review bucket policy before production use."; echo
    fi
}

# Run main function
main "$@"