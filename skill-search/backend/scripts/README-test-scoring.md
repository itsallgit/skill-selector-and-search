# Test Scoring & Ranking

This directory contains test scripts for analyzing the scoring and ranking algorithm behavior.

## Overview

The scoring test script provides detailed insights into:
1. **Vector Search Results** - Skills returned by semantic search
2. **User Filtering** - How users are matched against search results
3. **Scoring Calculations** - Detailed breakdown of score components
4. **Ranking Logic** - How users are ranked and score distribution

## Scripts

### test_scoring_and_ranking.py

Python script that queries the live backend API and provides comprehensive logging.

**Location:** `backend/scripts/test_scoring_and_ranking.py`

**Usage:**
```bash
# From within backend container
python /app/scripts/test_scoring_and_ranking.py "aws lambda"

# Via Docker from skill-search directory
docker-compose exec backend python /app/scripts/test_scoring_and_ranking.py "aws lambda"
```

**Options:**
- `query` - Required: Search query to test
- `--host` - Optional: API host (default: localhost)
- `--port` - Optional: API port (default: 8000)

### test-scoring.sh

Bash wrapper for easier command-line testing.

**Location:** `scripts/test-scoring.sh`

**Usage:**
```bash
# From skill-search directory
./scripts/test-scoring.sh "aws lambda"
./scripts/test-scoring.sh "container orchestration"
```

## Integration with project-setup.sh

The test script is integrated into the main project setup menu:

1. Run `./project-setup.sh` from project root
2. Select option 3: **Skill Search**
3. Select option 2: **Test Scoring & Ranking**
4. Enter your search query when prompted

## Output Explanation

### Step 1: Vector Search Results
Shows the skills returned by the semantic search, including:
- Query parameters
- Unique skills matched
- Top skills by similarity score

### Step 2: User Filtering & Matching
Shows how users are filtered:
- Total users evaluated
- Users with matches
- Match statistics (avg, max, min)

### Step 3: Scoring Details
For each top-ranked user, shows:
- **Overall Score** - Normalized score out of 100
- **Raw Score** - Actual calculated score before normalization
- **Skill Contributions** - Every matched skill with:
  - Skill title and hierarchy
  - Level (L1-L4)
  - User's rating (Beginner/Intermediate/Advanced)
  - Similarity percentage
  - Points contributed
  - Percentage of total score
- **Transfer Bonus** - Bonus for transferable technology experience
- **Scoring Calculation** - Formula explanation with example
- **Normalization Analysis** - Shows the normalization issue

### Step 4: Ranking Analysis
Shows:
- Score distribution (highest, lowest, average, range)
- Score categories (Excellent, Strong, Good, Fair, Weak)
- Ranking verification

### Executive Summary
Key findings including:
- Users with high similarity matches (≥75%)
- Low score alerts for users who should score higher
- Root cause identification

## Expected Issues to Identify

The test script is designed to highlight the **normalization problem**:

```
⚠️  LOW SCORE ALERT: Advanced rating + 77% match = only 7.7 score!
```

**Root Cause:**
The max_possible_score is calculated based on ALL skills returned by vector search (~20 skills), but most users only match a SUBSET of those skills. This creates artificially low normalized scores.

**Example:**
- User has 1 skill: "AWS Lambda" (L4) with Advanced rating (3)
- Similarity: 77% (0.77)
- Calculation: 0.77 × 0.3 (L4 weight) × 4.0 (Advanced) = 0.924 raw score
- Vector search returned 20 skills
- Max possible: ~22 points (20 skills × avg weight × max rating)
- Normalized: (0.924 / 22) × 100 = **4.2%**

**Expected for this scenario:**
A user with Advanced skill and 77% similarity should score 60-80/100, not <10/100.

## Next Steps

After running the test and analyzing the output:
1. Review the normalization analysis section
2. Identify users with unexpectedly low scores
3. Consider the proposed solutions:
   - Normalize by user's matched skills only
   - Adjust normalization scaling
   - Remove normalization entirely
   - Normalize by expected match count
