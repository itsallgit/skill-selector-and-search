#!/bin/bash

# =============================================================================
# S3 Bucket Operations Utilities
# =============================================================================
# Handles bucket creation, configuration, deletion, and management for both
# standard S3 buckets and S3 Vector buckets.

# Source required utilities (only if not already sourced)
if [ -z "$DEFAULT_REGION" ]; then
    UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$UTILS_DIR/config.sh"
    source "$UTILS_DIR/logging.sh"
    source "$UTILS_DIR/ui-prompts.sh"
fi

# =============================================================================
# BUCKET CREATION
# =============================================================================

# Create S3 bucket (general purpose or vector bucket)
create_bucket() {
    local bucket_name="$1"
    local bucket_type="${2:-main}"
    print_status "Creating S3 bucket: $bucket_name (type: $bucket_type)"
    
    if [ "$bucket_type" = "vector" ]; then
        # Check if vector bucket already exists
        print_status "Checking if vector bucket exists..."
        if aws s3vectors get-vector-bucket --vector-bucket-name "$bucket_name" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null; then
            print_warning "Vector bucket $bucket_name already exists (continuing)."
            return 0
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
            return 0
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

# =============================================================================
# BUCKET CONFIGURATION
# =============================================================================

# Configure bucket for static website hosting
configure_website_hosting() {
    local bucket_name="$1"
    print_status "Configuring static website hosting..."
    
    # Create website configuration using config function
    local config_file=$(mktemp)
    generate_website_config > "$config_file"
    
    aws s3api put-bucket-website \
        --bucket "$bucket_name" \
        --website-configuration "file://$config_file" \
        --profile "$AWS_PROFILE"
    
    rm "$config_file"
    
    print_success "Static website hosting configured"
}

# Set bucket policy for public read access
set_bucket_policy() {
    local bucket_name="$1"
    print_status "Setting bucket policy for public read access..."
    
    # Create bucket policy using config function
    local policy_file=$(mktemp)
    generate_bucket_policy "$bucket_name" > "$policy_file"
    
    aws s3api put-bucket-policy \
        --bucket "$bucket_name" \
        --policy "file://$policy_file" \
        --profile "$AWS_PROFILE"
    
    rm "$policy_file"
    
    print_success "Bucket policy set for public access"
}

# Disable block public access
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

# Configure CORS for client-side file operations
configure_cors() {
    local bucket_name="$1"
    print_status "Configuring CORS for client-side file operations..."
    
    # Create CORS configuration using config function
    local cors_file=$(mktemp)
    generate_cors_config > "$cors_file"
    
    aws s3api put-bucket-cors \
        --bucket "$bucket_name" \
        --cors-configuration "file://$cors_file" \
        --profile "$AWS_PROFILE"
    
    rm "$cors_file"
    
    print_success "CORS configuration applied"
}

# =============================================================================
# BUCKET DELETION
# =============================================================================

# List buckets matching a pattern
list_buckets_by_pattern() {
    local pattern="$1"
    local bucket_type="${2:-standard}"  # standard or vector
    local buckets=()
    
    if [ "$bucket_type" = "vector" ]; then
        while IFS= read -r bucket; do
            if [[ "$bucket" =~ ^${pattern}- ]] && [ -n "$bucket" ] && [ "$bucket" != "None" ]; then
                buckets+=("$bucket")
            fi
        done < <(aws s3vectors list-vector-buckets --region "$REGION" --profile "$AWS_PROFILE" --query 'vectorBuckets[].vectorBucketName' --output text 2>/dev/null | tr '\t' '\n')
    else
        while IFS= read -r bucket; do
            if [[ "$bucket" =~ ^${pattern} ]]; then
                buckets+=("$bucket")
            fi
        done < <(aws s3api list-buckets --profile "$AWS_PROFILE" --query 'Buckets[].Name' --output text 2>/dev/null | tr '\t' '\n')
    fi
    
    # Return array via stdout (one per line)
    for bucket in "${buckets[@]}"; do
        echo "$bucket"
    done
}

# Delete standard S3 bucket with all contents
delete_standard_bucket() {
    local bucket_name="$1"
    print_status "Deleting bucket: $bucket_name"
    
    # First, remove all objects and versions
    print_status "Removing all objects from $bucket_name..."
    aws s3 rm "s3://$bucket_name" --recursive --profile "$AWS_PROFILE" 2>/dev/null || true
    
    # Delete all versions if versioning is enabled
    aws s3api delete-objects --bucket "$bucket_name" --profile "$AWS_PROFILE" \
        --delete "$(aws s3api list-object-versions --bucket "$bucket_name" --profile "$AWS_PROFILE" \
        --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null)" 2>/dev/null || true
    
    # Delete all delete markers
    aws s3api delete-objects --bucket "$bucket_name" --profile "$AWS_PROFILE" \
        --delete "$(aws s3api list-object-versions --bucket "$bucket_name" --profile "$AWS_PROFILE" \
        --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null)" 2>/dev/null || true
    
    # Finally, delete the bucket itself
    if aws s3api delete-bucket --bucket "$bucket_name" --profile "$AWS_PROFILE" 2>/dev/null; then
        print_success "Bucket $bucket_name deleted successfully"
        return 0
    else
        print_error "Failed to delete bucket $bucket_name (it may have remaining objects or delete protection)"
        return 1
    fi
}

# Delete vector bucket
delete_vector_bucket() {
    local bucket_name="$1"
    print_status "Preparing to delete vector bucket: $bucket_name"
    
    # First, check if bucket has any indexes
    print_status "Checking for vector indexes in bucket..."
    local indexes=()
    while IFS= read -r index; do
        [ -n "$index" ] && [ "$index" != "None" ] && indexes+=("$index")
    done < <(list_vector_indexes "$bucket_name")
    
    if [ ${#indexes[@]} -gt 0 ]; then
        echo
        print_warning "Found ${#indexes[@]} vector index(es) in bucket $bucket_name:"
        for index in "${indexes[@]}"; do
            echo "  - $index"
        done
        echo
        
        print_warning "All indexes must be deleted before the bucket can be removed."
        if prompt_yes_no "Delete all indexes in this bucket?" "N"; then
            # Delete each index
            local failed_indexes=()
            for index in "${indexes[@]}"; do
                print_status "Deleting index: $index"
                if ! delete_vector_index "$bucket_name" "$index"; then
                    failed_indexes+=("$index")
                fi
            done
            
            if [ ${#failed_indexes[@]} -gt 0 ]; then
                echo
                print_error "Failed to delete the following indexes:"
                for index in "${failed_indexes[@]}"; do
                    echo "  - $index"
                done
                print_error "Cannot delete bucket $bucket_name until all indexes are removed"
                return 1
            fi
            
            print_success "All indexes deleted successfully"
        else
            print_warning "Bucket deletion cancelled. Indexes must be deleted first."
            return 1
        fi
    fi
    
    # Check for regular objects in the bucket (non-index data)
    print_status "Checking for objects in bucket..."
    local object_count=$(aws s3 ls "s3://$bucket_name" --profile "$AWS_PROFILE" --recursive 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$object_count" -gt 0 ]; then
        echo
        print_warning "Found $object_count object(s) in bucket $bucket_name"
        
        if prompt_yes_no "Delete all objects in this bucket?" "N"; then
            print_status "Deleting all objects from $bucket_name..."
            if aws s3 rm "s3://$bucket_name" --recursive --profile "$AWS_PROFILE" 2>&1; then
                print_success "All objects deleted successfully"
            else
                print_error "Failed to delete some objects"
                return 1
            fi
        else
            print_warning "Bucket deletion cancelled. All objects must be deleted first."
            return 1
        fi
    fi
    
    # Now attempt to delete the empty vector bucket
    echo
    print_status "Deleting vector bucket: $bucket_name"
    if aws s3vectors delete-vector-bucket --vector-bucket-name "$bucket_name" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null; then
        print_success "Vector bucket $bucket_name deleted successfully"
        return 0
    else
        print_error "Failed to delete vector bucket $bucket_name"
        print_status "The bucket may still have protected resources or require manual intervention"
        return 1
    fi
}

# Interactive bucket deletion workflow
delete_buckets_interactive() {
    local pattern="$1"
    local bucket_type="${2:-standard}"  # standard or vector
    local description="$3"
    
    print_status "Checking for existing $description buckets..."
    
    # Get list of buckets
    local existing_buckets=()
    while IFS= read -r bucket; do
        [ -n "$bucket" ] && existing_buckets+=("$bucket")
    done < <(list_buckets_by_pattern "$pattern" "$bucket_type")
    
    if [ ${#existing_buckets[@]} -eq 0 ]; then
        print_status "No existing $description buckets found."
        return 0
    fi
    
    echo
    print_warning "Found ${#existing_buckets[@]} existing $description bucket(s):"
    for bucket in "${existing_buckets[@]}"; do
        echo "  - $bucket"
    done
    echo
    
    if ! prompt_yes_no "Do you want to delete any of these buckets?" "N"; then
        print_status "Skipping bucket deletion."
        return 0
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
        return 0
    fi
    
    # Final confirmation
    echo
    print_warning "The following bucket(s) will be PERMANENTLY DELETED with ALL contents:"
    for bucket in "${delete_list[@]}"; do
        echo "  - $bucket"
    done
    echo
    
    if [ "$bucket_type" = "vector" ]; then
        print_warning "Note: Vector buckets with indexes will require additional confirmations for:"
        echo "  1. Deletion of all indexes in the bucket"
        echo "  2. Deletion of all objects in the bucket"
        echo "  3. Final bucket deletion"
        echo
    fi
    
    if prompt_dangerous_confirmation "DELETE" "permanently delete these buckets"; then
        # Delete each bucket
        local failed_deletions=()
        for bucket in "${delete_list[@]}"; do
            echo
            echo "════════════════════════════════════════════════════════"
            if [ "$bucket_type" = "vector" ]; then
                delete_vector_bucket "$bucket" || failed_deletions+=("$bucket")
            else
                delete_standard_bucket "$bucket" || failed_deletions+=("$bucket")
            fi
        done
        echo
        
        if [ ${#failed_deletions[@]} -gt 0 ]; then
            print_error "Failed to delete the following bucket(s):"
            for bucket in "${failed_deletions[@]}"; do
                echo "  - $bucket"
            done
            return 1
        else
            print_success "All selected buckets deleted successfully"
        fi
    else
        print_warning "Bucket deletion cancelled."
    fi
}

# =============================================================================
# BUCKET UTILITIES
# =============================================================================

# Get website URL for a bucket
get_website_url() {
    local bucket_name="$1"
    local website_url="http://$bucket_name.s3-website-$REGION.amazonaws.com"
    
    if [ "$REGION" = "us-east-1" ]; then
        website_url="http://$bucket_name.s3-website.amazonaws.com"
    fi
    
    echo "$website_url"
}

# Check if bucket exists (standard bucket)
bucket_exists() {
    local bucket_name="$1"
    aws s3api head-bucket --bucket "$bucket_name" --profile "$AWS_PROFILE" 2>/dev/null
}

# Check if vector bucket exists
vector_bucket_exists() {
    local bucket_name="$1"
    aws s3vectors get-vector-bucket --vector-bucket-name "$bucket_name" --region "$REGION" --profile "$AWS_PROFILE" 2>/dev/null
}

# =============================================================================
# VECTOR INDEX OPERATIONS
# =============================================================================

# Check if vector index exists in a vector bucket
vector_index_exists() {
    local bucket_name="$1"
    local index_name="$2"
    
    aws s3vectors get-index \
        --vector-bucket-name "$bucket_name" \
        --index-name "$index_name" \
        --region "$REGION" \
        --profile "$AWS_PROFILE" 2>/dev/null
}

# List all vector indexes in a vector bucket
list_vector_indexes() {
    local bucket_name="$1"
    
    aws s3vectors list-indexes \
        --vector-bucket-name "$bucket_name" \
        --region "$REGION" \
        --profile "$AWS_PROFILE" \
        --query 'indexes[].indexName' \
        --output text 2>/dev/null | tr '\t' '\n'
}

# Create vector index
create_vector_index() {
    local bucket_name="$1"
    local index_name="$2"
    local dimension="$3"
    local distance_metric="$4"
    local data_type="${5:-float32}"  # Default to float32 (only supported type)
    
    print_status "Creating vector index: $index_name"
    print_status "Configuration:"
    echo "  Bucket: $bucket_name"
    echo "  Index: $index_name"
    echo "  Data Type: $data_type"
    echo "  Dimension: $dimension"
    echo "  Distance Metric: $distance_metric"
    echo "  Region: $REGION"
    echo
    
    if aws s3vectors create-index \
        --vector-bucket-name "$bucket_name" \
        --index-name "$index_name" \
        --data-type "$data_type" \
        --dimension "$dimension" \
        --distance-metric "$distance_metric" \
        --region "$REGION" \
        --profile "$AWS_PROFILE" 2>&1; then
        print_success "Vector index '$index_name' created successfully"
        return 0
    else
        print_error "Failed to create vector index '$index_name'"
        return 1
    fi
}

# Delete vector index
delete_vector_index() {
    local bucket_name="$1"
    local index_name="$2"
    
    print_status "Deleting vector index: $index_name"
    
    if aws s3vectors delete-index \
        --vector-bucket-name "$bucket_name" \
        --index-name "$index_name" \
        --region "$REGION" \
        --profile "$AWS_PROFILE" 2>/dev/null; then
        print_success "Vector index '$index_name' deleted successfully"
        return 0
    else
        print_error "Failed to delete vector index '$index_name'"
        return 1
    fi
}

# Rename vector index by creating new one and noting the old name
rename_vector_index() {
    local bucket_name="$1"
    local old_index_name="$2"
    local new_index_name="$3"
    local dimension="$4"
    local distance_metric="$5"
    local data_type="${6:-float32}"
    
    print_status "Renaming vector index from '$old_index_name' to '$new_index_name'..."
    
    # Note: S3 Vectors doesn't support direct rename, so we document this limitation
    print_warning "Note: Vector indexes cannot be directly renamed in S3 Vectors."
    print_warning "The old index '$old_index_name' will remain. You may delete it manually if needed."
    
    # Create the new index with timestamp
    if create_vector_index "$bucket_name" "$new_index_name" "$dimension" "$distance_metric" "$data_type"; then
        print_success "New timestamped index created: $new_index_name"
        print_status "Original index preserved: $old_index_name"
        return 0
    else
        return 1
    fi
}

