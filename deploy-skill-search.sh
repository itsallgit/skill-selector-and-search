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

# Prompt user to reuse existing vector bucket
prompt_reuse_existing_bucket() {
    local existing_buckets=()
    while IFS= read -r bucket; do
        [ -n "$bucket" ] && existing_buckets+=("$bucket")
    done < <(list_buckets_by_pattern "$BUCKET_PREFIX_SKILL_VECTORS" "vector")
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        # No existing buckets, must create new
        return 1
    fi
    
    echo
    print_status "Found ${#existing_buckets[@]} existing vector bucket(s):"
    for bucket in "${existing_buckets[@]}"; do
        echo "  - $bucket"
    done
    echo
    
    if prompt_yes_no "Do you want to reuse an existing vector bucket?" "N"; then
        # Let user select which bucket
        if [ ${#existing_buckets[@]} -eq 1 ]; then
            BUCKET_NAME_SKILL_VECTORS="${existing_buckets[0]}"
            print_success "Using existing bucket: $BUCKET_NAME_SKILL_VECTORS"
        else
            echo "Select a bucket:"
            local index=1
            for bucket in "${existing_buckets[@]}"; do
                echo "  [$index] $bucket"
                ((index++))
            done
            
            while true; do
                read -p "Enter bucket number [1-${#existing_buckets[@]}]: " selection
                if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#existing_buckets[@]}" ]; then
                    BUCKET_NAME_SKILL_VECTORS="${existing_buckets[$((selection-1))]}"
                    print_success "Using existing bucket: $BUCKET_NAME_SKILL_VECTORS"
                    break
                else
                    print_warning "Invalid selection. Please try again."
                fi
            done
        fi
        return 0
    else
        return 1
    fi
}

# Manage vector index in the bucket
manage_vector_index() {
    local bucket_name="$1"
    
    print_subheader "Vector Index Configuration"
    
    # Check if index exists
    print_status "Checking for existing vector index..."
    
    if vector_index_exists "$bucket_name" "$VECTOR_INDEX_NAME"; then
        print_status "Found existing vector index: $VECTOR_INDEX_NAME"
        echo
        
        if prompt_yes_no "Do you want to preserve the existing vector index?" "N"; then
            # Rename with timestamp
            local timestamp=$(date +%Y%m%d-%H%M%S)
            local backup_index_name="${VECTOR_INDEX_NAME}-${timestamp}"
            
            print_status "Creating timestamped backup index: $backup_index_name"
            print_warning "Note: The original index '$VECTOR_INDEX_NAME' will remain unchanged."
            print_status "You will have both indexes: '$VECTOR_INDEX_NAME' (original) and '$backup_index_name' (new)"
            echo
            
            # Create new index with timestamp
            if create_vector_index "$bucket_name" "$backup_index_name" "$VECTOR_EMBEDDING_DIM" "$VECTOR_DISTANCE_METRIC" "$VECTOR_DATA_TYPE"; then
                print_success "New timestamped index created alongside the original"
                echo
                print_status "Active indexes in bucket:"
                list_vector_indexes "$bucket_name" | while read -r idx; do
                    echo "  - $idx"
                done
            else
                print_error "Failed to create timestamped index"
                return 1
            fi
        else
            # Delete and recreate with same name
            print_status "Deleting existing vector index..."
            if delete_vector_index "$bucket_name" "$VECTOR_INDEX_NAME"; then
                echo
                print_status "Creating new vector index with same name..."
                if create_vector_index "$bucket_name" "$VECTOR_INDEX_NAME" "$VECTOR_EMBEDDING_DIM" "$VECTOR_DISTANCE_METRIC" "$VECTOR_DATA_TYPE"; then
                    print_success "Vector index recreated successfully"
                else
                    print_error "Failed to create new vector index"
                    return 1
                fi
            else
                print_error "Failed to delete existing index"
                return 1
            fi
        fi
    else
        print_status "No existing vector index found."
        echo
        
        # Display configuration and confirm
        print_status "Vector Index Configuration:"
        echo "  Bucket Name: $bucket_name"
        echo "  Index Name: $VECTOR_INDEX_NAME"
        echo "  Data Type: $VECTOR_DATA_TYPE"
        echo "  Dimension: $VECTOR_EMBEDDING_DIM"
        echo "  Distance Metric: $VECTOR_DISTANCE_METRIC"
        echo "  Region: $REGION"
        echo
        
        if prompt_yes_no "Proceed with creating this vector index?" "Y"; then
            if create_vector_index "$bucket_name" "$VECTOR_INDEX_NAME" "$VECTOR_EMBEDDING_DIM" "$VECTOR_DISTANCE_METRIC" "$VECTOR_DATA_TYPE"; then
                print_success "Vector index created successfully"
            else
                print_error "Failed to create vector index"
                return 1
            fi
        else
            print_warning "Vector index creation cancelled"
            return 1
        fi
    fi
    
    return 0
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
    
    # Step 2: Check for existing buckets and offer deletion
    print_subheader "Existing Vector Buckets"
    delete_buckets_interactive "$BUCKET_PREFIX_SKILL_VECTORS" "vector" "$BUCKET_PREFIX_SKILL_VECTORS"
    
    # Step 3: Determine if reusing existing bucket or creating new one
    local reusing_bucket=0
    if prompt_reuse_existing_bucket; then
        reusing_bucket=1
        print_status "Reusing existing vector bucket: $BUCKET_NAME_SKILL_VECTORS"
    else
        # Set new bucket name
        BUCKET_NAME_SKILL_VECTORS="$DEFAULT_BUCKET_NAME_SKILL_VECTORS"
        print_status "Will create new vector bucket: $BUCKET_NAME_SKILL_VECTORS"
    fi
    
    echo
    
    # Step 4: Create bucket if needed
    if [ "$reusing_bucket" -eq 0 ]; then
        if ! create_bucket "$BUCKET_NAME_SKILL_VECTORS" "vector"; then
            print_error "Failed to create vector bucket"
            exit 1
        fi
    fi
    
    # Step 5: Manage vector index (create or update)
    if manage_vector_index "$BUCKET_NAME_SKILL_VECTORS"; then
        echo
        print_header "Deployment completed successfully!"
        
        echo "Vector Bucket Details:"
        echo "  Name: $BUCKET_NAME_SKILL_VECTORS"
        echo "  Region: $REGION"
        echo "  S3 URI: s3://$BUCKET_NAME_SKILL_VECTORS"
        echo
        echo "Vector Index Details:"
        echo "  Index Name: $VECTOR_INDEX_NAME"
        echo "  Dimension: $VECTOR_EMBEDDING_DIM"
        echo "  Distance Metric: $VECTOR_DISTANCE_METRIC"
        echo
        print_status "Next steps:"
        echo "  1. Run skill-embeddings.py to generate and upload skill vectors"
        echo "  2. Update VECTOR_BUCKET in skill-embeddings.py to: $BUCKET_NAME_SKILL_VECTORS"
        echo
    else
        echo
        print_header "Deployment completed with warnings."
        echo
    fi
}

# Run main function
main "$@"
