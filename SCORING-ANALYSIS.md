# Scoring Algorithm Analysis - AWS Lambda Query

## Summary

The test script has successfully identified the scoring normalization issue. When searching for "aws lambda", a user with an **Advanced rating (3)** and **76.7% similarity match** on "AWS Lambda" is scoring only **7.67/100**, when they should realistically score **50-80/100**.

## Test Results

### Query: "aws lambda"

**Vector Search Results:**
- 10 skills returned from semantic search
- Top match: AWS Lambda (76.69% similarity) ✅
- Only 5 of 10 skills were actually possessed by users

**User Rankings:**

| Rank | User | Score | Key Skill | Similarity | Rating | Issue |
|------|------|-------|-----------|------------|--------|-------|
| 1 | test04 | 10.86 | AWS (3 variations) | 39% | Advanced | Low score for multiple AWS skills |
| 2 | test03 | **7.67** | **AWS Lambda** | **76.7%** | **Advanced** | **🚨 CRITICAL ISSUE** |
| 3 | test02 | 5.27 | AWS Lambda | 76.7% | Beginner | Expected low score |
| 4 | test05 | 0.64 | AWS Cost Explorer | 26% | Beginner | Expected very low score |

## The Problem

### Rank #2: test03 - The Critical Case

**User Profile:**
- Has: AWS Lambda (L4/Technology level)
- Rating: Advanced (3)
- Parent skill: Serverless Architecture (L3)

**Scoring Calculation:**
```
Raw score = 0.7669 (similarity) × 0.3 (L4 weight) × 4.0 (Advanced multiplier) = 0.92 points
```

**Normalization (THE PROBLEM):**
```
Max possible score = 20 skills × avg weight × max rating = ~22 points
Normalized = (0.92 / 22) × 100 = 7.67/100
```

### Root Cause

The **max_possible_score** is calculated based on ALL 20 skills returned by vector search, assuming:
- Perfect similarity (1.0) for all skills
- Maximum rating (Advanced = 4.0) for all skills
- Each skill weighted appropriately

**However**, users typically only match 1-5 of those 20 skills, creating a denominator that is 4-20x too large!

## Expected vs Actual Behavior

### test03 with AWS Lambda (Advanced, 77% match):

**What we're getting:**
- Raw score: 0.92
- Normalized: 7.67/100
- Category: "Weak Match"

**What we should get:**
- A user with Advanced proficiency in the EXACT skill being searched
- With a 77% semantic match
- Should score: **60-80/100** ("Strong" or "Good Match")

### Why This Matters

1. **User Experience**: Finding someone with advanced AWS Lambda expertise should show them as a strong match, not weak
2. **Hiring/Resourcing**: Decision makers may skip over qualified candidates due to artificially low scores
3. **Trust**: The scoring system loses credibility when obvious matches score poorly

## The Math

### Current Formula:
```
max_possible = Σ(similarity=1.0 × level_weight × rating=4.0) for all 20 vector search results
             ≈ 20 skills × 0.3 avg weight × 4.0 = 24 points

normalized = (user_raw_score / 24) × 100
```

### Problem Illustrated:
- User has 1 perfect skill match: 0.92 points
- Max possible assumes 20 perfect matches: 24 points  
- Result: (0.92 / 24) × 100 = **3.8%** ❌

### What It Should Be:
- User has 1 skill match: 0.92 points
- Max possible for THEIR matches: ~1.2 points (assuming perfect similarity)
- Result: (0.92 / 1.2) × 100 = **77%** ✅

## Proposed Solutions

### Option 1: Normalize by User's Matched Skills Only ⭐ RECOMMENDED
**Change:** Calculate max_possible based only on the skills the user HAS, not all vector search results.

**Pros:**
- Fair comparison based on what the user brings
- Scores reflect quality of matches, not quantity
- User with 1 excellent match scores higher than user with 5 weak matches

**Cons:**
- Doesn't reward breadth of skills as much

**Implementation:**
```python
def _calculate_max_possible_score(self, user_matched_skills):
    """Calculate max based on USER'S skills, not all search results."""
    max_score = 0.0
    max_rating_multiplier = max(self.rating_multipliers.values())
    
    for skill in user_matched_skills:
        level = skill['level']
        level_weight = self.level_weights.get(level, 0.1)
        max_score += (1.0 * level_weight * max_rating_multiplier)
    
    return max_score
```

### Option 2: Use Expected Match Count
**Change:** Normalize based on an "expected" number of relevant skills (e.g., 5-7 skills).

**Pros:**
- Balances quality and quantity
- More predictable scoring ranges

**Cons:**
- Arbitrary threshold selection

### Option 3: Logarithmic/Square Root Scaling
**Change:** Apply non-linear scaling to compress the range.

**Pros:**
- Preserves relative rankings
- More distributed scores

**Cons:**
- Less intuitive
- Doesn't solve root cause

### Option 4: Remove Normalization
**Change:** Use raw scores directly and adjust weights.

**Pros:**
- Eliminates normalization issues
- Raw scores are meaningful

**Cons:**
- Requires recalibrating all weights
- Score ranges less predictable

## Recommendation

**Implement Option 1: Normalize by User's Matched Skills Only**

This is the most fair and intuitive approach. A user with:
- 1 skill at Advanced level with 77% match should score ~65-80%
- 3 skills at Advanced level with ~40% matches should score ~40-50%
- 5 skills at Beginner level should score ~20-30%

The current system unfairly penalizes users for NOT having skills that weren't even relevant to them.

## Next Steps

1. ✅ **Test script created** - Can now easily test any query
2. ⏳ **Review findings** - Confirm the analysis
3. ⏳ **Choose solution** - Select Option 1 or alternative
4. ⏳ **Implement fix** - Update `scoring.py`
5. ⏳ **Test changes** - Use test script to validate
6. ⏳ **Rebuild container** - Deploy changes

## How to Run the Test

### Via project-setup.sh (Interactive Menu):
```bash
./project-setup.sh
# Select: 3) Skill Search
# Select: 2) Test Scoring & Ranking
# Enter query: aws lambda
```

### Via Command Line:
```bash
cd skill-search
./scripts/test-scoring.sh "aws lambda"
```

### Directly in Container:
```bash
cd skill-search
docker-compose exec backend python /app/scripts/test_scoring_and_ranking.py "aws lambda"
```

## Test Cases to Try

1. **"aws lambda"** - Exact technology match (current analysis)
2. **"serverless architecture"** - L3 generic skill match
3. **"cloud solutions"** - L2 category match
4. **"python programming"** - Different skill domain
5. **"kubernetes docker"** - Multiple technologies

---

**Analysis Date:** 2025-10-16  
**Test Script:** `/skill-search/backend/scripts/test_scoring_and_ranking.py`  
**Scoring Logic:** `/skill-search/backend/services/scoring.py`
