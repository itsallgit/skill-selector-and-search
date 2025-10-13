#!/bin/bash

# =============================================================================
# Logging Utilities
# =============================================================================
# Provides colored output functions for consistent logging across deployment scripts.

# Source configuration for color codes (only if not already sourced)
if [ -z "$RED" ]; then
    UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$UTILS_DIR/config.sh"
fi

# Print informational message
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print confirmation/attention message
print_confirm() {
    echo -e "${RED}[ATTENTION]${NC} $1"
}

# Print section header
print_header() {
    echo
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo
}

# Print subsection header
print_subheader() {
    echo
    echo "-------- $1 --------"
    echo
}
