#!/bin/bash

# =============================================================================
# Skills Selector Application - AWS S3 Deployment Script
# =============================================================================
# This script deploys the Skills Selector web application to AWS S3.
# It creates/uses an S3 bucket, configures it for static website hosting,
# sets up CORS for client-side file operations, and deploys the application.

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared utilities
source "$SCRIPT_DIR/scripts/config.sh"
source "$SCRIPT_DIR/scripts/logging.sh"
source "$SCRIPT_DIR/scripts/ui-prompts.sh"
source "$SCRIPT_DIR/scripts/aws-auth.sh"
source "$SCRIPT_DIR/scripts/bucket-operations.sh"

# =============================================================================
# SKILL SELECTOR SPECIFIC FUNCTIONS
# =============================================================================

# Prompt for existing bucket usage
prompt_existing_bucket() {
    if prompt_yes_no "Deploy to an existing bucket?" "N"; then
        while true; do
            local existing_bucket
            existing_bucket=$(prompt_text "Enter existing bucket name" "" "non-empty")
            
            if bucket_exists "$existing_bucket"; then
                BUCKET_NAME_SKILL_SELECTOR="$existing_bucket"
                local bucket_region
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

# Update application configuration
update_app_config() {
    print_status "Updating application configuration..."
    
    # Update the bucket name in app.js
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/bucketName: '[^']*'/bucketName: '$BUCKET_NAME_SKILL_SELECTOR'/g" "$SKILL_SELECTOR_DIR/app.js"
        sed -i '' "s/region: '[^']*'/region: '$REGION'/g" "$SKILL_SELECTOR_DIR/app.js"
    else
        # Linux
        sed -i "s/bucketName: '[^']*'/bucketName: '$BUCKET_NAME_SKILL_SELECTOR'/g" "$SKILL_SELECTOR_DIR/app.js"
        sed -i "s/region: '[^']*'/region: '$REGION'/g" "$SKILL_SELECTOR_DIR/app.js"
    fi
    
    print_success "Application configuration updated"
}

# Deploy files to S3
deploy_files() {
    print_status "Deploying application files to S3..."
    
    # Deploy skill-selector web application files
    print_status "Deploying web application files from $SKILL_SELECTOR_DIR/..."
    
    for file_entry in "${SKILL_SELECTOR_FILES[@]}"; do
        IFS=':' read -r file content_type <<< "$file_entry"
        aws s3 cp "$SKILL_SELECTOR_DIR/$file" "s3://$BUCKET_NAME_SKILL_SELECTOR/$file" \
            --content-type "$content_type" \
            --profile "$AWS_PROFILE"
    done
    
    # Deploy data files
    print_status "Deploying data files from $DATA_DIR/..."
    
    for file_entry in "${DATA_FILES[@]}"; do
        IFS=':' read -r file content_type <<< "$file_entry"
        aws s3 cp "$DATA_DIR/$file" "s3://$BUCKET_NAME_SKILL_SELECTOR/$file" \
            --content-type "$content_type" \
            --profile "$AWS_PROFILE"
    done
    
    print_success "Files deployed successfully"
}

# Deploy to existing bucket (preserving user data)
deploy_to_existing_bucket() {
    print_status "Deploying to existing bucket (preserving users-master.json and /users directory)..."
    
    # Deploy web application files
    for file_entry in "${SKILL_SELECTOR_FILES[@]}"; do
        IFS=':' read -r file content_type <<< "$file_entry"
        aws s3 cp "$SKILL_SELECTOR_DIR/$file" "s3://$BUCKET_NAME_SKILL_SELECTOR/$file" \
            --content-type "$content_type" \
            --profile "$AWS_PROFILE" 2>/dev/null || true
    done
    
    # Deploy data files (excluding users-master.json to preserve existing)
    for file_entry in "${DATA_FILES[@]}"; do
        IFS=':' read -r file content_type <<< "$file_entry"
        
        # Skip users-master.json to preserve existing user data
        if [ "$file" = "users-master.json" ]; then
            continue
        fi
        
        aws s3 cp "$DATA_DIR/$file" "s3://$BUCKET_NAME_SKILL_SELECTOR/$file" \
            --content-type "$content_type" \
            --profile "$AWS_PROFILE" 2>/dev/null || true
    done
    
    print_success "Files deployed (users-master.json and /users directory preserved)"
}

# =============================================================================
# MAIN DEPLOYMENT FUNCTION
# =============================================================================

main() {
    print_header "Skills Selector - AWS Deployment"
    
    # Step 1: AWS Authentication
    select_aws_profile
    check_aws_cli
    
    echo
    
    # Step 2: Check for existing buckets and offer deletion
    delete_buckets_interactive "$BUCKET_PREFIX_SKILL_SELECTOR" "standard" "$BUCKET_PREFIX_SKILL_SELECTOR"
    
    # Step 3: Choose deployment target (new or existing bucket)
    prompt_existing_bucket
    
    # Set bucket name if creating new
    if [ "$USING_EXISTING_BUCKET" = "0" ]; then
        BUCKET_NAME_SKILL_SELECTOR="$DEFAULT_BUCKET_NAME_SKILL_SELECTOR"
    fi
    
    # Step 4: Confirm deployment
    print_status "Starting deployment with the following configuration:"
    echo "  Bucket Name: $BUCKET_NAME_SKILL_SELECTOR"
    [ "$USING_EXISTING_BUCKET" = "1" ] && echo "  (Existing bucket mode)"
    echo "  Region: $REGION"
    echo "  AWS Profile: $AWS_PROFILE"
    echo
    
    if ! prompt_yes_no "Proceed with deployment?" "N"; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    # Step 5: Create/configure bucket
    if [ "$USING_EXISTING_BUCKET" = "0" ]; then
        create_bucket "$BUCKET_NAME_SKILL_SELECTOR" "main"
        disable_block_public_access "$BUCKET_NAME_SKILL_SELECTOR"
        set_bucket_policy "$BUCKET_NAME_SKILL_SELECTOR"
        configure_website_hosting "$BUCKET_NAME_SKILL_SELECTOR"
        configure_cors "$BUCKET_NAME_SKILL_SELECTOR"
    else
        print_status "Existing bucket mode: skipping bucket creation & configuration."
    fi
    
    # Step 6: Update application configuration
    update_app_config
    
    # Step 7: Deploy files
    if [ "$USING_EXISTING_BUCKET" = "1" ]; then
        deploy_to_existing_bucket
    else
        deploy_files
    fi
    
    # Step 8: Success message
    echo
    print_header "Deployment completed successfully!"
    
    echo "Application URL:"
    echo -e "${GREEN}$(get_website_url "$BUCKET_NAME_SKILL_SELECTOR")${NC}"
    echo
    
    print_warning "Security Note: Public access enabled. Review bucket policy before production use."
    echo
}

# Run main function
main "$@"
