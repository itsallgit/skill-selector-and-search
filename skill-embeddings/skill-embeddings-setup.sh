#!/bin/bash
################################################################################
# Skill Embeddings - Setup & Configuration
# ==============================================================================
# Interactive setup script for configuring AWS profiles and vector bucket
# for skill embeddings generation and testing.
#
# This script:
#   1. Discovers available AWS profiles
#   2. Prompts user to select profiles for Bedrock and S3 Vectors
#   3. Lists available S3 Vector buckets and prompts for selection
#   4. Generates skill-embeddings-config.json
#   5. Provides menu to generate or test embeddings
#
# Usage:
#   ./skill-embeddings-setup.sh
################################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration file path
CONFIG_FILE="${SCRIPT_DIR}/skill-embeddings-config.json"

# Python scripts
GENERATE_SCRIPT="${SCRIPT_DIR}/scripts/skill-embeddings.py"
TEST_SCRIPT="${SCRIPT_DIR}/scripts/test-skill-embeddings.py"

# Source shared utilities
source "${SCRIPT_DIR}/../shared/script-utils/logging.sh"
source "${SCRIPT_DIR}/../shared/script-utils/ui-prompts.sh"

# Colors
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"

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
    local purpose="$1"  # "Bedrock" or "S3 Vectors"
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
        echo "Please run 'Provision Vector Bucket & Index' first from the Skill Embeddings menu"
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
# Generate Configuration File
################################################################################
generate_config() {
    local bedrock_profile="$1"
    local bedrock_region="$2"
    local s3_profile="$3"
    local s3_region="$4"
    local vector_bucket="$5"
    local vector_index="${6:-skills-index}"
    
    print_status "Generating configuration file: $CONFIG_FILE"
    
    cat > "$CONFIG_FILE" << EOF
{
  "bedrock_profile": "$bedrock_profile",
  "bedrock_region": "$bedrock_region",
  "s3vectors_profile": "$s3_profile",
  "s3vectors_region": "$s3_region",
  "vector_bucket": "$vector_bucket",
  "vector_index": "$vector_index"
}
EOF
    
    print_success "Configuration file created successfully"
    echo ""
    print_status "Configuration:"
    echo "  Bedrock Profile: $bedrock_profile (Region: $bedrock_region)"
    echo "  S3 Vectors Profile: $s3_profile (Region: $s3_region)"
    echo "  Vector Bucket: $vector_bucket"
    echo "  Vector Index: $vector_index"
    echo ""
}

################################################################################
# Show Operations Menu
################################################################################
show_operations_menu() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              SKILL EMBEDDINGS - OPERATIONS MENU                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
    
    echo -e "${BOLD}Select an operation:${RESET}"
    echo ""
    echo "  1) Generate Skill Embeddings    - Create embeddings and upload to S3"
    echo "  2) Test Skill Embeddings        - Test semantic search"
    echo ""
    echo "  3) Exit"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

################################################################################
# Execute Python Script
################################################################################
execute_python_script() {
    local script_name="$1"
    local script_path="$2"
    
    echo ""
    echo -e "${GREEN}${BOLD}Starting: ${script_name}${RESET}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${RESET}"
    echo ""
    
    if [ ! -f "$script_path" ]; then
        print_error "Script not found: $script_path"
        return 1
    fi
    
    python3 "$script_path"
    local exit_code=$?
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        print_success "$script_name completed successfully"
    else
        print_error "$script_name failed with exit code: $exit_code"
    fi
    echo ""
    
    return $exit_code
}

################################################################################
# Handle Operations Menu
################################################################################
handle_operations() {
    while true; do
        # Clear any lingering input
        while read -r -t 0; do read -r; done 2>/dev/null
        
        show_operations_menu
        local choice=""
        read -r -p "Enter your choice (1-3): " choice </dev/tty
        echo ""
        
        case "$choice" in
            1)
                execute_python_script "Generate Skill Embeddings" "$GENERATE_SCRIPT"
                read -r -p "Press Enter to continue..." </dev/tty
                ;;
            2)
                execute_python_script "Test Skill Embeddings" "$TEST_SCRIPT"
                read -r -p "Press Enter to continue..." </dev/tty
                ;;
            3)
                echo ""
                echo -e "${GREEN}Exiting...${RESET}"
                echo ""
                return 0
                ;;
            *)
                echo ""
                echo -e "${YELLOW}Invalid selection. Please choose 1-3.${RESET}"
                echo ""
                sleep 2
                ;;
        esac
    done
}

################################################################################
# Main Setup Function
################################################################################
main() {
    clear
    print_header "Skill Embeddings - Setup & Configuration"
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        echo "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Get available profiles
    local profiles=()
    while IFS= read -r profile; do
        profiles+=("$profile")
    done < <(get_aws_profiles)
    
    if [ ${#profiles[@]} -eq 0 ]; then
        print_error "No AWS profiles found"
        echo "Please configure AWS profiles using: aws configure --profile <profile-name>"
        exit 1
    fi
    
    # Ask if user wants same profile for everything or separate
    echo ""
    print_status "AWS Profile Configuration"
    echo ""
    echo "You can use:"
    echo "  - Same profile for both Bedrock and S3 Vectors"
    echo "  - Separate profiles (e.g., if Bedrock access requires different credentials)"
    echo ""
    
    local use_same_profile="N"
    if prompt_yes_no "Use the same AWS profile for both Bedrock and S3 Vectors?" "Y"; then
        use_same_profile="Y"
    fi
    
    local bedrock_profile=""
    local bedrock_region=""
    local s3_profile=""
    local s3_region=""
    
    if [ "$use_same_profile" = "Y" ]; then
        # Select single profile
        bedrock_profile=$(select_profile "both Bedrock and S3 Vectors" "${profiles[@]}")
        bedrock_region=$(get_profile_region "$bedrock_profile")
        s3_profile="$bedrock_profile"
        s3_region="$bedrock_region"
        
        print_success "Using profile '$bedrock_profile' for both services"
    else
        # Select separate profiles
        bedrock_profile=$(select_profile "Bedrock" "${profiles[@]}")
        bedrock_region=$(get_profile_region "$bedrock_profile")
        print_success "Using profile '$bedrock_profile' for Bedrock (Region: $bedrock_region)"
        
        s3_profile=$(select_profile "S3 Vectors" "${profiles[@]}")
        s3_region=$(get_profile_region "$s3_profile")
        print_success "Using profile '$s3_profile' for S3 Vectors (Region: $s3_region)"
    fi
    
    # Select vector bucket
    echo ""
    print_status "Vector Bucket Selection"
    local vector_bucket=$(select_vector_bucket "$s3_profile" "$s3_region")
    print_success "Selected bucket: $vector_bucket"
    
    # Generate configuration file
    echo ""
    generate_config "$bedrock_profile" "$bedrock_region" "$s3_profile" "$s3_region" "$vector_bucket" "skills-index"
    
    # Show operations menu
    print_success "Setup complete! You can now generate or test embeddings."
    sleep 2
    
    handle_operations
}

# Run main function
main "$@"
