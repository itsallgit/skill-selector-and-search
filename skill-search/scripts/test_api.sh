#!/bin/bash
#
# Quick API Test Script (using curl)
#
# Simple shell script to test Skills Search API endpoints
# Requires: curl, jq (optional, for pretty JSON)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST=${1:-localhost}
PORT=${2:-8000}
BASE_URL="http://${HOST}:${PORT}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Skills Search API Quick Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Testing: $BASE_URL"
echo ""

# Check if jq is available
if command -v jq &> /dev/null; then
    JQ_AVAILABLE=true
    FORMAT="jq ."
else
    JQ_AVAILABLE=false
    FORMAT="cat"
    echo -e "${YELLOW}⚠ jq not installed - JSON output will not be formatted${NC}"
    echo -e "${YELLOW}  Install with: brew install jq${NC}"
    echo ""
fi

# Test 1: Root endpoint
echo -e "${BLUE}[1/5] Testing Root Endpoint${NC}"
if curl -sf "$BASE_URL" | $FORMAT > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Root endpoint OK${NC}"
    curl -sf "$BASE_URL" | $FORMAT
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
    exit 1
fi
echo ""

# Test 2: Health check
echo -e "${BLUE}[2/5] Testing Health Check${NC}"
if response=$(curl -sf "$BASE_URL/api/health"); then
    echo -e "${GREEN}✓ Health check OK${NC}"
    echo "$response" | $FORMAT
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Test 3: Statistics
echo -e "${BLUE}[3/5] Testing Statistics${NC}"
if response=$(curl -sf "$BASE_URL/api/stats"); then
    echo -e "${GREEN}✓ Statistics OK${NC}"
    echo "$response" | $FORMAT
else
    echo -e "${RED}✗ Statistics failed${NC}"
    exit 1
fi
echo ""

# Test 4: Search
echo -e "${BLUE}[4/5] Testing Search Endpoint${NC}"
echo "Query: 'AWS Lambda and serverless architecture'"
if response=$(curl -sf -X POST "$BASE_URL/api/search" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "AWS Lambda and serverless architecture",
        "top_k_skills": 5,
        "top_n_users": 3
    }'); then
    echo -e "${GREEN}✓ Search OK${NC}"
    
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$response" | jq '{
            matched_skills: .matched_skills | length,
            top_users: .top_users | length,
            buckets: .buckets | map({name, count}),
            sample_user: .top_users[0] | {name, email, score}
        }'
    else
        echo "$response"
    fi
else
    echo -e "${RED}✗ Search failed${NC}"
    exit 1
fi
echo ""

# Test 5: User detail (try to get from search results)
echo -e "${BLUE}[5/5] Testing User Detail Endpoint${NC}"
if search_result=$(curl -sf -X POST "$BASE_URL/api/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "cloud", "top_k_skills": 5, "top_n_users": 1}'); then
    
    if [ "$JQ_AVAILABLE" = true ]; then
        email=$(echo "$search_result" | jq -r '.top_users[0].email // empty')
    else
        # Simple grep/cut approach if jq not available
        email=$(echo "$search_result" | grep -o '"email":"[^"]*"' | head -1 | cut -d'"' -f4)
    fi
    
    if [ -n "$email" ]; then
        echo "Testing with user: $email"
        if response=$(curl -sf "$BASE_URL/api/users/$email"); then
            echo -e "${GREEN}✓ User detail OK${NC}"
            
            if [ "$JQ_AVAILABLE" = true ]; then
                echo "$response" | jq '{
                    name,
                    email,
                    total_skills,
                    l1_count: .l1_skills | length,
                    l2_count: .l2_skills | length,
                    l3_count: .l3_skills | length,
                    l4_count: .l4_skills | length
                }'
            else
                echo "$response"
            fi
        else
            echo -e "${RED}✗ User detail failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ No users found to test with${NC}"
    fi
else
    echo -e "${RED}✗ Could not perform search to get user${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All API endpoints working!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo "  - Open frontend: http://${HOST}:3000"
echo "  - View API docs: ${BASE_URL}/docs"
echo "  - Run full tests: python3 test_api.py"
echo ""
