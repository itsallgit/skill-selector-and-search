#!/bin/bash
################################################################################
# Test Scoring & Ranking - Standalone Wrapper
# ==============================================================================
# Wrapper script to run the scoring test from anywhere
#
# Usage:
#   ./test-scoring.sh "aws lambda"
#   ./test-scoring.sh "container orchestration"
################################################################################

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"

# Check if query provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No search query provided${RESET}"
    echo ""
    echo "Usage: $0 \"search query\""
    echo ""
    echo "Examples:"
    echo "  $0 \"aws lambda\""
    echo "  $0 \"container orchestration\""
    echo ""
    exit 1
fi

QUERY="$1"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              TEST SCORING & RANKING                                          ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

echo -e "${GREEN}Query: '${QUERY}'${RESET}"
echo ""

# Check if backend container is running
if ! docker-compose ps backend | grep -q "Up"; then
    echo -e "${RED}Error: Backend container is not running${RESET}"
    echo ""
    echo "Please start the backend first:"
    echo "  cd skill-search"
    echo "  docker-compose up -d backend"
    echo ""
    exit 1
fi

echo -e "${GREEN}Running test...${RESET}"
echo ""

# Run the test
docker-compose exec backend python /app/scripts/test_scoring_and_ranking.py "$QUERY"

echo ""
echo -e "${GREEN}${BOLD}Test completed!${RESET}"
echo ""
