#!/bin/bash
################################################################################
# Skills Selector and Search - Project Setup
# ==============================================================================
# Interactive menu system for deploying and managing project components
#
# Usage:
#   ./project-setup.sh
#
# Components:
#   1. Skill Selector    - User skill assessment application
#   2. Skill Embeddings  - Generate semantic embeddings for skills
#   3. Skill Search      - Semantic search for users by skills
################################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Component paths
SKILL_SELECTOR_SETUP="${SCRIPT_DIR}/skill-selector/infra/deploy-skill-selector.sh"
SKILL_EMBEDDINGS_INFRA="${SCRIPT_DIR}/skill-embeddings/infra/deploy-skill-embeddings.sh"
SKILL_EMBEDDINGS_SETUP="${SCRIPT_DIR}/skill-embeddings/skill-embeddings-setup.sh"
SKILL_SEARCH_SETUP="${SCRIPT_DIR}/skill-search/skill-search-setup.sh"

# Utility scripts
BANNER_SCRIPT="${SCRIPT_DIR}/shared/script-utils/banner.sh"

# Source shared utilities for logging
source "${SCRIPT_DIR}/shared/script-utils/logging.sh"

# Colors
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"

################################################################################
# Display Main Menu
################################################################################
show_menu() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗                                ║
║   ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝                                ║
║   ███████╗█████╔╝ ██║██║     ██║     ███████╗                                ║
║   ╚════██║██╔═██╗ ██║██║     ██║     ╚════██║                                ║
║   ███████║██║  ██╗██║███████╗███████╗███████║                                ║
║   ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝                                ║
║                                                                              ║
║              SELECTOR & SEARCH - PROJECT SETUP                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
    
    echo -e "${BOLD}Select a component to deploy or manage:${RESET}"
    echo ""
    echo "  1) Skill Selector      - Deploy user skill assessment application"
    echo "  2) Skill Embeddings    - Generate semantic embeddings for skills"
    echo "  3) Skill Search        - Deploy semantic search application"
    echo ""
    echo "  4) Exit"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

################################################################################
# Display Skill Embeddings Submenu
################################################################################
show_skill_embeddings_menu() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              SKILL EMBEDDINGS - MANAGEMENT MENU                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
    
    echo -e "${BOLD}Select an operation:${RESET}"
    echo ""
    echo "  1) Provision Vector Bucket & Index  - Setup AWS infrastructure"
    echo "  2) Setup & Run Embeddings           - Configure profiles and generate/test"
    echo ""
    echo "  3) Return to Main Menu"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

################################################################################
# Execute Component Script
################################################################################
execute_component() {
    local component_name="$1"
    local script_path="$2"
    local is_python="${3:-false}"
    
    echo -e "${GREEN}${BOLD}Starting: ${component_name}${RESET}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${RESET}"
    echo ""
    
    # Check if script exists
    if [ ! -f "$script_path" ]; then
        echo -e "${YELLOW}✗ Script not found: ${script_path}${RESET}"
        echo ""
        read -p "Press Enter to return to menu..."
        return 1
    fi
    
    # Make sure script is executable
    chmod +x "$script_path"
    
    # Execute the script and capture exit code
    set +e  # Don't exit on error - we want to show banner
    if [ "$is_python" = "true" ]; then
        python3 "$script_path"
    else
        "$script_path"
    fi
    local exit_code=$?
    set -e
    
    # Show banner with result
    echo ""
    echo ""
    bash "$BANNER_SCRIPT" "$component_name" "$exit_code"
    
    # Wait for user to acknowledge and clear input buffer
    read -r -p "" </dev/tty
    
    return $exit_code
}

################################################################################
# Handle Skill Embeddings Submenu
################################################################################
handle_skill_embeddings() {
    local submenu_choice=""
    while true; do
        # Clear any lingering input
        while read -r -t 0; do read -r; done 2>/dev/null
        
        show_skill_embeddings_menu
        submenu_choice=""
        read -r -p "Enter your choice (1-3): " submenu_choice </dev/tty
        echo ""
        
        case "$submenu_choice" in
            1)
                execute_component "Provision Vector Bucket & Index" "$SKILL_EMBEDDINGS_INFRA" false
                ;;
            2)
                execute_component "Setup & Run Embeddings" "$SKILL_EMBEDDINGS_SETUP" false
                ;;
            3)
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
# Handle Menu Selection
################################################################################
handle_selection() {
    local choice="$1"
    
    case $choice in
        1)
            execute_component "Skill Selector" "$SKILL_SELECTOR_SETUP" false
            ;;
        2)
            handle_skill_embeddings
            ;;
        3)
            execute_component "Skill Search" "$SKILL_SEARCH_SETUP" false
            ;;
        4)
            echo ""
            echo -e "${GREEN}Thank you for using Skills Selector & Search!${RESET}"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo -e "${YELLOW}Invalid selection. Please choose 1-4.${RESET}"
            echo ""
            sleep 2
            ;;
    esac
}

################################################################################
# Main Loop
################################################################################
main() {
    local main_choice=""
    while true; do
        # Clear any lingering input
        while read -r -t 0; do read -r; done 2>/dev/null
        
        show_menu
        main_choice=""
        read -r -p "Enter your choice (1-4): " main_choice </dev/tty
        echo ""
        handle_selection "$main_choice"
    done
}

# Run main
main
