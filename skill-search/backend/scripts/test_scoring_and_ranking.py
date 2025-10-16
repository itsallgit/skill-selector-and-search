#!/usr/bin/env python3
"""
Test Scoring and Ranking Logic

This script tests the skill search API and provides detailed logging of:
1. Skills returned by vector search
2. User filtering and matching
3. Scoring calculations with breakdown
4. Final ranking results

Usage:
    python test_scoring_and_ranking.py [query] [--host HOST] [--port PORT]
    
Examples:
    python test_scoring_and_ranking.py "aws lambda"
    python test_scoring_and_ranking.py "container orchestration" --host localhost --port 8000
"""

import argparse
import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime


class ScoringTestHarness:
    """Test harness for analyzing scoring and ranking behavior."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize test harness with API endpoint."""
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api"
        
    def print_header(self, text: str, char: str = "="):
        """Print a formatted header."""
        width = 80
        print(f"\n{char * width}")
        print(f"{text.center(width)}")
        print(f"{char * width}\n")
    
    def print_section(self, text: str):
        """Print a section header."""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}\n")
    
    def test_api_health(self) -> bool:
        """Test if the API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                if status == 'healthy':
                    print("✓ API is healthy and accessible")
                    return True
                else:
                    print(f"✗ API health check failed: status={status}")
                    return False
            else:
                print(f"✗ API health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot connect to API: {e}")
            return False
    
    def search_skills(self, query: str) -> Dict[str, Any]:
        """Execute a skill search and return full response."""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Search failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    
    def analyze_vector_search_results(self, data: Dict[str, Any]):
        """Analyze and display vector search results."""
        self.print_section("STEP 1: Vector Search Results")
        
        # Get matched skills from vector search (available in response)
        matched_skills = data.get('matched_skills', [])
        
        print("Vector search executed with parameters:")
        print(f"  • Top K Skills: Configured in backend (typically 20)")
        print(f"  • Min Similarity: Configured in backend (typically 0.35)")
        print(f"  • Skills returned from vector search: {len(matched_skills)}")
        
        # Show top matched skills from vector search
        if matched_skills:
            print("\n  Top skills from vector search (sorted by similarity):")
            for i, skill in enumerate(matched_skills[:10], 1):
                title = skill.get('title', 'Unknown')
                level = skill.get('level', 0)
                similarity = skill.get('similarity', 0)
                level_name = {1: "L1-Category", 2: "L2-SubCat", 3: "L3-Generic", 4: "L4-Tech"}.get(level, f"L{level}")
                print(f"    {i:2d}. {title:40s} [{level_name}] Similarity: {similarity:.2%}")
        
        # Also analyze unique skills matched across all users
        all_user_matched_skills = set()
        for user in data.get('top_users', []):
            for skill in user.get('matched_skills', []):
                skill_id = skill.get('skill_id')
                if skill_id:
                    all_user_matched_skills.add(skill_id)
        
        print(f"\n  • Skills that users actually have: {len(all_user_matched_skills)} of {len(matched_skills)}")
    
    def analyze_user_filtering(self, data: Dict[str, Any]):
        """Analyze user filtering and matching."""
        self.print_section("STEP 2: User Filtering & Matching")
        
        top_users = data.get('top_users', [])
        buckets = data.get('buckets', [])
        
        # Calculate total users from buckets (buckets is a list of dicts)
        total_users = sum(bucket.get('count', 0) for bucket in buckets)
        if total_users == 0:
            total_users = len(top_users)
        
        print(f"Total users with matches: {len(top_users)}")
        
        # Show match statistics
        match_counts = [len(u.get('matched_skills', [])) 
                       for u in top_users]
        
        if match_counts:
            print(f"\nMatch statistics:")
            print(f"  • Average matched skills per user: {sum(match_counts) / len(match_counts):.1f}")
            print(f"  • Max matched skills: {max(match_counts)}")
            print(f"  • Min matched skills: {min(match_counts)}")
        
        # Show bucket distribution
        if buckets:
            print(f"\nScore distribution by category:")
            for bucket in buckets:
                name = bucket.get('name', 'Unknown')
                count = bucket.get('count', 0)
                print(f"  • {name}: {count} users")
    
    def analyze_scoring_details(self, data: Dict[str, Any], top_n: int = 5):
        """Analyze scoring details for top N users."""
        self.print_section(f"STEP 3: Scoring Details (Top {top_n} Users)")
        
        top_users = data.get('top_users', [])
        
        for i, user in enumerate(top_users[:top_n], 1):
            self.print_user_score_detail(user, rank=i)
    
    def print_user_score_detail(self, user: Dict[str, Any], rank: int):
        """Print detailed scoring breakdown for a single user."""
        email = user.get('email', 'Unknown')
        name = user.get('name', 'Unknown')
        
        # Get two-dimensional score components
        coverage_score = user.get('coverage_score', 0)
        coverage_percentage = user.get('coverage_percentage', 0)
        expertise_multiplier = user.get('expertise_multiplier', 1.0)
        expertise_label = user.get('expertise_label', 'Unknown')
        raw_score = user.get('raw_score', 0)
        display_score = user.get('display_score', 0)
        
        print(f"\n{'═' * 80}")
        print(f"RANK #{rank}: {name} ({email})")
        print(f"{'═' * 80}")
        
        # PRIMARY METRICS - Coverage and Expertise
        print(f"\n📊 TWO-DIMENSIONAL SCORE:")
        print(f"   COVERAGE:   {coverage_percentage:6.2f}%  (breadth of relevant skills)")
        print(f"   EXPERTISE:  {expertise_label:12s} ({expertise_multiplier:.2f}×)  (proficiency level)")
        print(f"")
        print(f"   Raw Score:     {raw_score:.4f}  (coverage × expertise)")
        print(f"   Display Score: {display_score:.2f}/100  (scaled to top user)")
        
        # Get score breakdown
        breakdown = user.get('score_breakdown', {})
        total_matched = breakdown.get('total_matched_skills', 0)
        
        print(f"\n   Total Matched Skills: {total_matched}")
        
        # Skill contributions
        contributions = breakdown.get('skill_contributions', [])
        if contributions:
            print(f"\n📚 MATCHED SKILLS BREAKDOWN (All {len(contributions)} skills):")
            print(f"{'─' * 80}")
            print(f"{'Skill':<38} {'Sim':<6} {'Weight':<8} {'Rating':<10} {'Cov%':<6}")
            print(f"{'─' * 80}")
            
            for skill in contributions:
                title = skill.get('title', 'Unknown')[:36]
                similarity = skill.get('similarity', 0)
                relevancy_weight = skill.get('relevancy_weight', 0)
                rating = skill.get('rating', 0)
                rating_name = {1: "Beginner", 2: "Intermed", 3: "Advanced"}.get(rating, str(rating))
                coverage_pct = skill.get('coverage_percentage', 0)
                
                print(f"{title:<38} {similarity:<6.0%} {relevancy_weight:<8.4f} {rating_name:<10} {coverage_pct:>5.1f}%")
        
        # Calculate scoring components
        print(f"\n🧮 SCORING ALGORITHM:")
        print(f"   Formula: Coverage × Expertise")
        print(f"")
        print(f"   Coverage = Σ(similarity²) for each matched skill")
        print(f"            = {coverage_score:.4f} raw")
        print(f"            = {coverage_percentage:.2f}% of maximum possible")
        print(f"")
        print(f"   Expertise = Weighted average rating multiplier")
        print(f"             • Beginner (1): 1.0×")
        print(f"             • Intermediate (2): 3.0×")
        print(f"             • Advanced (3): 6.0×")
        print(f"             = {expertise_multiplier:.2f}× ({expertise_label})")
        print(f"")
        print(f"   Raw Score = {coverage_score:.4f} × {expertise_multiplier:.2f} = {raw_score:.4f}")
        print(f"   Display = (raw / top_raw) × 100 = {display_score:.2f}/100")
    
    def analyze_ranking_logic(self, data: Dict[str, Any]):
        """Analyze the ranking logic and distribution."""
        self.print_section("STEP 4: Ranking Analysis")
        
        top_users = data.get('top_users', [])
        
        if not top_users:
            print("No results to analyze.")
            return
        
        display_scores = [u.get('display_score', 0) for u in top_users]
        raw_scores = [u.get('raw_score', 0) for u in top_users]
        coverage_percentages = [u.get('coverage_percentage', 0) for u in top_users]
        expertise_labels = [u.get('expertise_label', 'Unknown') for u in top_users]
        
        print(f"Score Distribution:")
        print(f"  • Highest Display Score: {max(display_scores):.2f}")
        print(f"  • Lowest Display Score: {min(display_scores):.2f}")
        print(f"  • Average Display Score: {sum(display_scores) / len(display_scores):.2f}")
        print(f"  • Score Range: {max(display_scores) - min(display_scores):.2f}")
        
        print(f"\nCoverage Distribution:")
        print(f"  • Highest Coverage: {max(coverage_percentages):.2f}%")
        print(f"  • Lowest Coverage: {min(coverage_percentages):.2f}%")
        print(f"  • Average Coverage: {sum(coverage_percentages) / len(coverage_percentages):.2f}%")
        
        print(f"\nExpertise Distribution:")
        expertise_counts = {}
        for label in expertise_labels:
            expertise_counts[label] = expertise_counts.get(label, 0) + 1
        for label, count in sorted(expertise_counts.items()):
            print(f"  • {label}: {count} users")
        
        # Score buckets
        excellent = sum(1 for s in display_scores if s >= 80)
        strong = sum(1 for s in display_scores if 60 <= s < 80)
        good = sum(1 for s in display_scores if 40 <= s < 60)
        other = sum(1 for s in display_scores if s < 40)
        
        print(f"\nDisplay Score Categories:")
        print(f"  • Excellent (80-100): {excellent} users")
        print(f"  • Strong (60-79): {strong} users")
        print(f"  • Good (40-59): {good} users")
        print(f"  • Other (<40): {other} users")
        
        # Check for ranking issues
        print(f"\nRanking Verification:")
        is_sorted = all(raw_scores[i] >= raw_scores[i+1] for i in range(len(raw_scores)-1))
        if is_sorted:
            print(f"  ✓ Users are correctly ranked by raw score (descending)")
        else:
            print(f"  ✗ WARNING: Users are NOT correctly ranked!")
    
    def generate_summary(self, data: Dict[str, Any], query: str):
        """Generate executive summary of findings."""
        self.print_section("EXECUTIVE SUMMARY")
        
        top_users = data.get('top_users', [])
        
        if not top_users:
            print("No matches found for this query.")
            return
        
        # Key metrics
        total_users = len(top_users)
        display_scores = [u.get('display_score', 0) for u in top_users]
        coverage_percentages = [u.get('coverage_percentage', 0) for u in top_users]
        avg_display_score = sum(display_scores) / len(display_scores) if display_scores else 0
        avg_coverage = sum(coverage_percentages) / len(coverage_percentages) if coverage_percentages else 0
        top_display_score = max(display_scores) if display_scores else 0
        
        # Find users with high coverage and advanced expertise
        high_quality_users = []
        for user in top_users:
            coverage_pct = user.get('coverage_percentage', 0)
            expertise_label = user.get('expertise_label', '')
            display_score = user.get('display_score', 0)
            
            # High quality = good coverage (>40%) OR advanced expertise
            if coverage_pct >= 40 or expertise_label in ['Advanced', 'Expert']:
                high_quality_users.append({
                    'user': user.get('name', 'Unknown'),
                    'email': user.get('email', 'Unknown'),
                    'coverage_percentage': coverage_pct,
                    'expertise_label': expertise_label,
                    'display_score': display_score,
                    'matched_count': len(user.get('matched_skills', []))
                })
        
        print(f"Query: '{query}'")
        print(f"Total Matches: {total_users}")
        print(f"Average Display Score: {avg_display_score:.2f}/100")
        print(f"Average Coverage: {avg_coverage:.2f}%")
        print(f"Top Display Score: {top_display_score:.2f}/100")
        
        if high_quality_users:
            print(f"\n🎯 High Quality Matches (Coverage ≥40% OR Advanced+ Expertise):")
            for item in high_quality_users[:5]:
                print(f"   • {item['user']} ({item['email']})")
                print(f"     Coverage: {item['coverage_percentage']:.1f}% | Expertise: {item['expertise_label']}")
                print(f"     Matched Skills: {item['matched_count']} | Display Score: {item['display_score']:.2f}/100")
        
        print(f"\n💡 TWO-DIMENSIONAL SCORING:")
        print(f"   Coverage measures breadth - how many relevant skills the user has")
        print(f"   Expertise measures depth - proficiency level across matched skills")
        print(f"   Raw Score = Coverage × Expertise (used for ranking)")
        print(f"   Display Score = Scaled to make top user = 100 (for UI presentation)")
    
    def run_test(self, query: str):
        """Run complete test suite."""
        self.print_header(f"Scoring & Ranking Test: '{query}'")
        
        print(f"Test Configuration:")
        print(f"  • API Endpoint: {self.api_url}")
        print(f"  • Query: '{query}'")
        print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test API health
        self.print_section("API Health Check")
        if not self.test_api_health():
            print("\n❌ Cannot proceed with tests - API is not accessible")
            print("   Ensure the backend container is running: docker-compose up backend")
            sys.exit(1)
        
        # Execute search
        print("\nExecuting search...")
        data = self.search_skills(query)
        
        # Run analysis steps
        self.analyze_vector_search_results(data)
        self.analyze_user_filtering(data)
        self.analyze_scoring_details(data, top_n=5)
        self.analyze_ranking_logic(data)
        self.generate_summary(data, query)
        
        # Final output
        self.print_header("Test Complete", char="=")
        print(f"✓ Test completed successfully")
        print(f"  Results analyzed for {len(data.get('top_users', []))} users")
        print(f"  Review the detailed output above to identify scoring issues")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test skill search scoring and ranking logic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "aws lambda"
  %(prog)s "container orchestration" --host localhost --port 8000
  %(prog)s "python" --host 192.168.1.100
        """
    )
    
    parser.add_argument(
        'query',
        help='Search query to test (e.g., "aws lambda")'
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
    
    args = parser.parse_args()
    
    # Run test
    harness = ScoringTestHarness(host=args.host, port=args.port)
    try:
        harness.run_test(args.query)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
