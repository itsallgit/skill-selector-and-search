#!/bin/bash

# =============================================================================
# AWS Authentication and Configuration Utilities
# =============================================================================
# Handles AWS CLI profile selection, credential validation, and region detection.

# Source required utilities (only if not already sourced)
if [ -z "$DEFAULT_REGION" ]; then
    UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$UTILS_DIR/config.sh"
    source "$UTILS_DIR/logging.sh"
    source "$UTILS_DIR/ui-prompts.sh"
fi

# Select AWS CLI profile
select_aws_profile() {
    print_status "Detecting available AWS CLI profiles..."
    
    # Collect profiles into array (bash 3 compatible)
    local profiles=()
    while IFS= read -r p; do
        [ -n "$p" ] && profiles+=("$p")
    done <<EOF
$(aws configure list-profiles 2>/dev/null || true)
EOF

    if [ ${#profiles[@]} -eq 0 ]; then
        print_error "No AWS profiles found. Configure one with: aws configure --profile <name>"
        exit 1
    fi

    echo "Available AWS profiles:"
    for p in "${profiles[@]}"; do
        echo "  - $p"
    done

    while true; do
        local input_profile
        input_profile=$(prompt_text "Enter the profile name to use" "" "non-empty")
        
        local match_found="false"
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
        REGION="$DEFAULT_REGION"
        print_warning "No region configured in profile. Using default: $REGION"
        echo
        
        if prompt_yes_no "Would you like to use a different region?" "N"; then
            local custom_region
            custom_region=$(prompt_text "Enter AWS region (e.g., ap-southeast-2, us-east-1)" "" "non-empty")
            REGION="$custom_region"
            print_success "Using custom region: $REGION"
        fi
    fi
}

# Check AWS CLI installation and configuration
check_aws_cli() {
    print_status "Checking AWS CLI installation and configuration..."
    
    if ! command -v aws &>/dev/null; then
        print_error "AWS CLI is not installed. Install it first (brew install awscli / apt / yum)."
        exit 1
    fi
    
    # Check AWS CLI version
    local aws_version
    aws_version=$(aws --version 2>&1)
    print_status "AWS CLI version: $aws_version"
    
    if [ -z "$AWS_PROFILE" ]; then
        print_error "AWS profile not set (internal script error)."
        exit 1
    fi
    
    if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &>/dev/null; then
        print_error "Invalid AWS credentials for profile '$AWS_PROFILE'. Run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    print_success "AWS CLI is properly configured for profile '$AWS_PROFILE'"
}

# Check if s3vectors command is available
check_s3vectors_availability() {
    print_status "Checking for s3vectors command availability..."
    
    if aws s3vectors help &>/dev/null 2>&1; then
        print_success "s3vectors command is available"
        return 0
    else
        print_warning "s3vectors command not found or not available in this region/account"
        print_warning "S3 Vectors is a preview feature. Ensure:"
        print_warning "  1. Your AWS CLI is up to date (version 2.15.0 or later recommended)"
        print_warning "  2. You have preview access enabled for S3 Vectors"
        print_warning "  3. Your region supports S3 Vectors (check AWS documentation)"
        echo
        
        if prompt_yes_no "Continue anyway?" "N"; then
            return 0
        else
            print_error "Operation cancelled. Please update AWS CLI or enable S3 Vectors preview."
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
