#!/usr/bin/env python3
"""
Skills Search API Test Script

Tests all backend API endpoints to verify the application is working correctly.

Usage:
    python test_api.py [--host HOST] [--port PORT]

Examples:
    python test_api.py
    python test_api.py --host localhost --port 8000
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any
from datetime import datetime

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_success(message: str):
    """Print success message in green."""
    print(f"{GREEN}✓{NC} {message}")


def print_error(message: str):
    """Print error message in red."""
    print(f"{RED}✗{NC} {message}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{BLUE}ℹ{NC} {message}")


def print_warning(message: str):
    """Print warning message in yellow."""
    print(f"{YELLOW}⚠{NC} {message}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")


def test_health_endpoint(base_url: str) -> bool:
    """Test the health check endpoint."""
    print_section("Testing Health Check Endpoint")
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {data.get('status', 'unknown')}")
            print_success(f"Version: {data.get('version', 'unknown')}")
            print_success(f"User count: {data.get('user_count', 0)}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to health endpoint: {str(e)}")
        return False


def test_stats_endpoint(base_url: str) -> bool:
    """Test the statistics endpoint."""
    print_section("Testing Statistics Endpoint")
    
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Total users: {data.get('total_users', 0)}")
            print_success(f"Total skills: {data.get('total_skills', 0)}")
            
            skills_by_level = data.get('skills_by_level', {})
            print_info("Skills by level:")
            for level, count in sorted(skills_by_level.items()):
                print(f"  L{level}: {count}")
            
            skills_by_rating = data.get('skills_by_rating', {})
            print_info("Skills by rating:")
            for rating, count in sorted(skills_by_rating.items()):
                rating_name = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}.get(int(rating), "Unknown")
                print(f"  {rating_name} ({rating}): {count}")
            
            config = data.get('config', {})
            print_info("Configuration loaded successfully")
            
            return True
        else:
            print_error(f"Stats check failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to stats endpoint: {str(e)}")
        return False


def test_search_endpoint(base_url: str, query: str = "AWS Lambda and serverless architecture") -> bool:
    """Test the search endpoint."""
    print_section(f"Testing Search Endpoint")
    print_info(f"Query: '{query}'")
    
    try:
        payload = {
            "query": query,
            "top_k_skills": 10,
            "top_n_users": 5
        }
        
        response = requests.post(
            f"{base_url}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            matched_skills = data.get('matched_skills', [])
            top_users = data.get('top_users', [])
            buckets = data.get('buckets', [])
            
            print_success(f"Found {len(matched_skills)} matching skills")
            
            # Display top 3 matched skills
            if matched_skills:
                print_info("Top matched skills:")
                for i, skill in enumerate(matched_skills[:3], 1):
                    similarity = skill.get('similarity', 0)
                    color = skill.get('color', '')
                    print(f"  {i}. {skill.get('title', 'Unknown')} (L{skill.get('level', '?')}) - {similarity:.2%} {color}")
            
            print_success(f"Found {len(top_users)} top users")
            
            # Display top 3 users
            if top_users:
                print_info("Top users:")
                for user in top_users[:3]:
                    score = user.get('score', 0)
                    name = user.get('name', 'Unknown')
                    email = user.get('email', 'unknown@example.com')
                    matched = len(user.get('matched_skills', []))
                    transfer = user.get('transfer_bonus', 0)
                    
                    bonus_text = f" (+{transfer*100:.1f}% transfer)" if transfer > 0 else ""
                    print(f"  #{user.get('rank', '?')}. {name} ({email}) - Score: {score:.1f}{bonus_text}, {matched} skills")
            
            # Display bucket summary
            if buckets:
                print_info("Score buckets:")
                for bucket in buckets:
                    count = bucket.get('count', 0)
                    name = bucket.get('name', 'Unknown')
                    min_score = bucket.get('min_score', 0)
                    max_score = bucket.get('max_score', 100)
                    if count > 0:
                        print(f"  {name} ({min_score:.0f}-{max_score:.0f}): {count} users")
            
            return True
        else:
            print_error(f"Search failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to search endpoint: {str(e)}")
        return False


def test_user_detail_endpoint(base_url: str, email: str = None) -> bool:
    """Test the user detail endpoint."""
    print_section("Testing User Detail Endpoint")
    
    # If no email provided, try to get one from stats
    if not email:
        try:
            response = requests.get(f"{base_url}/api/stats", timeout=5)
            if response.status_code == 200:
                # Try to get a user from search results
                search_response = requests.post(
                    f"{base_url}/api/search",
                    json={"query": "cloud", "top_k_skills": 5, "top_n_users": 1},
                    timeout=10
                )
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    top_users = search_data.get('top_users', [])
                    if top_users:
                        email = top_users[0].get('email')
        except:
            pass
    
    if not email:
        print_warning("No email provided and couldn't find a user to test with")
        return False
    
    print_info(f"Testing with email: {email}")
    
    try:
        response = requests.get(f"{base_url}/api/users/{email}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"User: {data.get('name', 'Unknown')}")
            print_success(f"Email: {data.get('email', 'unknown')}")
            print_success(f"Total skills: {data.get('total_skills', 0)}")
            
            print_info("Skills breakdown:")
            print(f"  L1 (Categories): {len(data.get('l1_skills', []))}")
            print(f"  L2 (Sub-categories): {len(data.get('l2_skills', []))}")
            print(f"  L3 (Skills): {len(data.get('l3_skills', []))}")
            print(f"  L4 (Technologies): {len(data.get('l4_skills', []))}")
            
            return True
        elif response.status_code == 404:
            print_warning(f"User not found: {email}")
            return False
        else:
            print_error(f"User detail failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to user detail endpoint: {str(e)}")
        return False


def test_root_endpoint(base_url: str) -> bool:
    """Test the root endpoint."""
    print_section("Testing Root Endpoint")
    
    try:
        response = requests.get(base_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Service: {data.get('service', 'unknown')}")
            print_success(f"Version: {data.get('version', 'unknown')}")
            print_info(f"Docs available at: {data.get('docs', '/docs')}")
            print_info(f"Health check at: {data.get('health', '/api/health')}")
            return True
        else:
            print_error(f"Root endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to root endpoint: {str(e)}")
        return False


def run_all_tests(base_url: str) -> bool:
    """Run all API tests."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Skills Search API Test Suite{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    print(f"Testing backend at: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint(base_url)))
    
    # Test health endpoint
    results.append(("Health Check", test_health_endpoint(base_url)))
    
    # Test stats endpoint
    results.append(("Statistics", test_stats_endpoint(base_url)))
    
    # Test search endpoint with different queries
    results.append(("Search (AWS)", test_search_endpoint(base_url, "AWS Lambda and serverless architecture")))
    results.append(("Search (Cloud)", test_search_endpoint(base_url, "cloud computing and infrastructure")))
    
    # Test user detail endpoint
    results.append(("User Detail", test_user_detail_endpoint(base_url)))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = f"{GREEN}PASS{NC}" if result else f"{RED}FAIL{NC}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BLUE}{'='*60}{NC}")
    if failed == 0:
        print(f"{GREEN}✓ All tests passed! ({passed}/{len(results)}){NC}")
        print(f"{BLUE}{'='*60}{NC}\n")
        return True
    else:
        print(f"{RED}✗ Some tests failed ({passed}/{len(results)} passed, {failed} failed){NC}")
        print(f"{BLUE}{'='*60}{NC}\n")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Skills Search API endpoints"
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='API host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API port (default: 8000)'
    )
    parser.add_argument(
        '--email',
        help='Email address to test user detail endpoint with'
    )
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    try:
        success = run_all_tests(base_url)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{NC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
