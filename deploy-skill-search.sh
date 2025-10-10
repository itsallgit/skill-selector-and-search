#!/bin/bash

# =============================================================================
# Skills Search Backend - AWS S3 Vector Bucket Deployment Script
# =============================================================================
# This script provisions the infrastructure required for the Skills Search
# semantic search capability, including S3 Vector buckets for storing
# skill embeddings and supporting vector search operations.

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
# SKILL SEARCH SPECIFIC FUNCTIONS
# =============================================================================

# Interactive vector bucket management workflow
manage_vector_bucket_workflow() {
    print_header "Vector Bucket Setup"
    
    print_status "The vector bucket stores embedded skill vectors for semantic search."
    echo
    
    # List existing vector buckets
    print_status "Checking for existing $BUCKET_PREFIX_SKILL_VECTORS buckets in region $REGION..."
    echo
    
    local existing_buckets=()
    while IFS= read -r bucket; do
        [ -n "$bucket" ] && existing_buckets+=("$bucket")
    done < <(list_buckets_by_pattern "$BUCKET_PREFIX_SKILL_VECTORS" "vector")
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        print_status "No existing $BUCKET_PREFIX_SKILL_VECTORS buckets found in region $REGION."
        echo
    else
        print_status "Found ${#existing_buckets[@]} existing $BUCKET_PREFIX_SKILL_VECTORS bucket(s):"
        local index=1
        for bucket in "${existing_buckets[@]}"; do
            echo "  [$index] $bucket"
            ((index++))
        done
        echo
        
        # Ask if user wants to delete any buckets
        if prompt_yes_no "Do you want to delete any of these buckets?" "N"; then
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
                
                if prompt_dangerous_confirmation "DELETE" "permanently delete these vector buckets"; then
                    # Delete each bucket
                    for bucket in "${delete_list[@]}"; do
                        delete_vector_bucket "$bucket"
                        
                        # Remove from existing_buckets array
                        existing_buckets=("${existing_buckets[@]/$bucket}")
                    done
                    echo
                fi
            fi
        fi
    fi
    
    # Ask if user wants to create a new vector bucket
    echo
    if ! prompt_yes_no "Do you want to create a new vector bucket?" "Y"; then
        print_warning "Skipping vector bucket creation."
        return 1
    fi
    
    return 0
}

# Deploy vector bucket
deploy_vector_bucket() {
    print_status "Starting vector bucket deployment..."
    print_status "Vector Bucket Name: $BUCKET_NAME_SKILL_VECTORS"
    print_status "Region: $REGION"
    print_status "AWS Profile: $AWS_PROFILE"
    echo
    
    # Create vector bucket
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
        
        return 0
    else
        print_error "Vector bucket deployment failed!"
        return 1
    fi
}

# =============================================================================
# MAIN DEPLOYMENT FUNCTION
# =============================================================================

main() {
    print_header "Skills Search - AWS Vector Bucket Deployment"
    
    # Step 1: AWS Authentication
    select_aws_profile
    check_aws_cli
    check_s3vectors_availability
    
    # Step 2: Set bucket name
    BUCKET_NAME_SKILL_VECTORS="$DEFAULT_BUCKET_NAME_SKILL_VECTORS"
    
    # Step 3: Interactive workflow (list, delete, create)
    if manage_vector_bucket_workflow; then
        echo
        
        # Step 4: Deploy vector bucket
        if deploy_vector_bucket; then
            echo
            print_header "Vector bucket deployment completed successfully!"
            
            echo "Vector Bucket Details:"
            echo "  Name: $BUCKET_NAME_SKILL_VECTORS"
            echo "  Region: $REGION"
            echo "  S3 URI: s3://$BUCKET_NAME_SKILL_VECTORS"
            echo
        fi
    else
        echo
        print_header "No deployments were performed."
        echo
    fi
}

# Run main function
main "$@"
