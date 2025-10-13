#!/bin/bash
################################################################################
# Banner Utility
# ==============================================================================
# Displays ASCII art banner with status information for returning to main menu
#
# Usage:
#   banner.sh "Component Name" EXIT_CODE
#
# Example:
#   banner.sh "Skill Search Setup" 0
#   banner.sh "Skill Embeddings Generator" 1
#
# Arguments:
#   $1 - Component/script name (required)
#   $2 - Exit code from previous script (required)
################################################################################

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: banner.sh <component_name> <exit_code>"
    exit 1
fi

COMPONENT_NAME="$1"
EXIT_CODE="$2"

# Determine status message and color
if [ "$EXIT_CODE" -eq 0 ]; then
    STATUS="COMPLETED SUCCESSFULLY"
    STATUS_SYMBOL="✓"
    COLOR="\033[0;32m"  # Green
else
    STATUS="FAILED"
    STATUS_SYMBOL="✗"
    COLOR="\033[0;31m"  # Red
fi

RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[0;36m"

# Display banner
echo ""
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
echo -e "${CYAN}║${RESET}                     ${BOLD}RETURNING TO PROJECT SETUP MENU${RESET}                        ${CYAN}║${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════════════╣${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
# Calculate the component name line with proper padding
COMPONENT_TEXT="  Previous Component: ${COMPONENT_NAME}"
COMPONENT_LEN=${#COMPONENT_TEXT}
PADDING_LEN=$((76 - COMPONENT_LEN))
echo -e "${CYAN}║${RESET}  Previous Component: ${BOLD}${COMPONENT_NAME}${RESET}$(printf "%${PADDING_LEN}s")${CYAN}║${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
# Calculate the status line with proper padding
STATUS_TEXT="  Status: ${STATUS_SYMBOL} ${STATUS}"
STATUS_LEN=${#STATUS_TEXT}
PADDING_LEN=$((76 - STATUS_LEN))
echo -e "${CYAN}║${RESET}  Status: ${COLOR}${STATUS_SYMBOL} ${STATUS}${RESET}$(printf "%${PADDING_LEN}s")${CYAN}║${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
# Calculate the exit code line with proper padding
EXIT_TEXT="  Exit Code: ${EXIT_CODE}"
EXIT_LEN=${#EXIT_TEXT}
PADDING_LEN=$((76 - EXIT_LEN))
echo -e "${CYAN}║${RESET}  Exit Code: ${EXIT_CODE}$(printf "%${PADDING_LEN}s")${CYAN}║${RESET}"
echo -e "${CYAN}║                                                                            ║${RESET}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Additional message based on exit code
if [ "$EXIT_CODE" -ne 0 ]; then
    echo -e "${COLOR}${BOLD}⚠  The component script encountered an error.${RESET}"
    echo -e "${COLOR}${BOLD}⚠  Review the output above for troubleshooting information.${RESET}"
    echo ""
fi

echo -e "${BOLD}Press Enter to continue to the menu...${RESET}"
