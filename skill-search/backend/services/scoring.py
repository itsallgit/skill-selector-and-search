"""
Scoring Service - Implements the user ranking algorithm.

SCORING ALGORITHM DOCUMENTATION
================================

The scoring algorithm ranks users based on their skill alignment with search query results.
It considers multiple factors to produce a fair, weighted score.

Components:
-----------
1. **Skill Level Weights** - How much each hierarchy level contributes
   - L1 (Categories): 0.1 - Very broad, minimal weight
   - L2 (Sub-categories): 0.2 - Broader context
   - L3 (Generic Skills): 0.5 - MOST IMPORTANT - Core competencies
   - L4 (Technologies): 0.3 - Specific tools/tech

2. **User Rating Multipliers** - User's self-assessed proficiency (EXPONENTIAL)
   - Beginner (1): 1.0x
   - Intermediate (2): 2.0x  
   - Advanced (3): 4.0x
   
   Rationale: Advanced users with relevant L3 skills should rank higher than
   Intermediate users even if the latter have more specific L4 tool matches.

3. **Similarity Score** - From vector search (0-1 scale)
   - Derived from cosine distance: similarity = 1 - distance
   - Measures how semantically close the skill is to the query

4. **Transfer Bonus** - Credit for related technology experience
   - If query matches an L3 skill, but user only has the L4 technology
     under a DIFFERENT L3, they get partial credit
   - Example: Query matches "Serverless Architecture (L3) > AWS (L4)"
              User has "Cloud Security (L3) > AWS (L4)" 
              → User gets transfer bonus for AWS competence
   - Bonus: 0.02 per transferable technology, capped at 0.15 (15%)
   - Ensures users with relevant tech but different context aren't overlooked

Scoring Formula:
----------------
For each matched skill:
    
    base_score = similarity × level_weight × rating_multiplier
    
User total score:
    
    raw_score = Σ(base_score for all matched skills) + transfer_bonus
    normalized_score = (raw_score / max_possible_score) × 100

Ranking Order (Example):
------------------------
Query: "Container Orchestration (L3) + Kubernetes (L4)"

1. User C: Has Kubernetes (L4) under Container Orchestration (L3)
   → Direct L3 + L4 match = HIGHEST score

2. User B: Has Docker (L4) under Container Orchestration (L3)
   → Direct L3 match + different L4 = HIGH score

3. User A: Has Kubernetes (L4) under DevOps (different L3)
   → No L3 match, but gets transfer bonus = MEDIUM score
   → Ranks above users with NO relevant skills

The transfer bonus prevents User A from outranking Users B or C
(who have actual L3 matches), while ensuring they rank above users
with no relevant experience.

"""

from typing import List, Dict, Any, Set, Tuple
from config import settings
import logging

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring and ranking users based on matched skills."""
    
    def __init__(self):
        """Initialize scoring configuration from settings."""
        # Level weights
        self.level_weights = {
            1: settings.level_weight_l1,
            2: settings.level_weight_l2,
            3: settings.level_weight_l3,
            4: settings.level_weight_l4,
        }
        
        # Rating multipliers (exponential)
        self.rating_multipliers = {
            1: settings.rating_multiplier_1,
            2: settings.rating_multiplier_2,
            3: settings.rating_multiplier_3,
        }
        
        # Transfer bonus configuration
        self.transfer_bonus_per_tech = settings.transfer_bonus_per_tech
        self.transfer_bonus_cap = settings.transfer_bonus_cap
    
    def calculate_user_score(
        self,
        user: Dict[str, Any],
        matched_skills: List[Dict[str, Any]],
        skills_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive score for a user against matched skills.
        
        Args:
            user: User object with skills data
            matched_skills: List of skills from vector search
            skills_lookup: Full skills lookup table for hierarchy info
            
        Returns:
            Dictionary with score breakdown:
            {
                'raw_score': float,
                'normalized_score': float (0-100),
                'matched_skills_detail': List[Dict],
                'tech_matches': int,
                'transfer_bonus': float,
                'has_transfer_bonus': bool
            }
        """
        user_email = user.get('userEmail', user.get('email', 'unknown'))
        logger.debug(f"Calculating score for user: {user_email}")
        
        raw_score = 0.0
        matched_skills_detail = []
        tech_matches = 0
        transfer_bonus_amount = 0.0
        transfer_bonus_details = []  # Track details for modal
        
        # Build user skill lookups for efficient matching
        user_skills_map = self._build_user_skills_map(user)
        logger.debug(f"User {user_email} has skills: {list(user_skills_map.keys())[:10]}")  # Log first 10
        
        # Calculate max possible score (for normalization)
        max_possible = self._calculate_max_possible_score(matched_skills)
        
        # Score each matched skill
        for matched_skill in matched_skills:
            skill_id = matched_skill['skill_id']
            level = matched_skill['level']
            similarity = matched_skill['similarity']
            
            # Check if user has this skill
            if skill_id in user_skills_map:
                user_skill = user_skills_map[skill_id]
                rating = user_skill['rating']
                
                # Calculate base score for this skill
                skill_score = (
                    similarity *
                    self.level_weights.get(level, 0.1) *
                    self.rating_multipliers.get(rating, 1.0)
                )
                
                raw_score += skill_score
                
                # Track details
                matched_skills_detail.append({
                    'skill_id': skill_id,
                    'title': matched_skill['title'],
                    'level': level,
                    'rating': rating,
                    'similarity': similarity,
                    'skill_score': skill_score,
                    'match_type': 'direct'
                })
                
                # Count technology matches (L4)
                if level == 4:
                    tech_matches += 1
        
        # Calculate transfer bonus
        transfer_bonus_result = self._calculate_transfer_bonus(
            user,
            matched_skills,
            user_skills_map,
            skills_lookup
        )
        
        transfer_bonus_amount = transfer_bonus_result['bonus']
        transfer_bonus_details = transfer_bonus_result['details']
        
        raw_score += transfer_bonus_amount
        
        # Normalize score to 0-100
        if max_possible > 0:
            normalized_score = min(100.0, (raw_score / max_possible) * 100)
        else:
            normalized_score = 0.0
        
        return {
            'raw_score': raw_score,
            'normalized_score': round(normalized_score, 2),
            'matched_skills_detail': matched_skills_detail,
            'tech_matches': tech_matches,
            'transfer_bonus': round(transfer_bonus_amount, 4),
            'has_transfer_bonus': transfer_bonus_amount > 0,
            'transfer_bonus_details': transfer_bonus_details
        }
    
    def _build_user_skills_map(self, user: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Build efficient lookup map of user's skills.
        
        Returns:
            {skill_id: {rating: int, level: int, title: str}}
        """
        skills_map = {}
        
        # Log the user structure to understand what we're working with
        user_keys = list(user.keys())
        logger.debug(f"Building skills map for user with keys: {user_keys}")
        
        # Handle both 'skills' (processed) and 'selectedSkills' (raw) formats
        user_skills = user.get('skills', user.get('selectedSkills', []))
        logger.debug(f"User has {len(user_skills)} skills")
        
        for skill in user_skills:
            skill_id = skill.get('skill_id')
            if skill_id:
                skills_map[skill_id] = {
                    'rating': skill.get('rating', 1),
                    'level': skill.get('skill_level', 0),
                    'title': skill.get('skill_title', ''),
                    'parent_ids': skill.get('parent_ids', [])
                }
        
        logger.debug(f"Built skills map with {len(skills_map)} skills")
        return skills_map
    
    def _calculate_max_possible_score(self, matched_skills: List[Dict[str, Any]]) -> float:
        """
        Calculate maximum possible score (for normalization).
        Assumes perfect similarity (1.0) and max rating (3).
        """
        max_score = 0.0
        max_rating_multiplier = max(self.rating_multipliers.values())
        
        for skill in matched_skills:
            level = skill['level']
            level_weight = self.level_weights.get(level, 0.1)
            max_score += (1.0 * level_weight * max_rating_multiplier)
        
        return max_score
    
    def _calculate_transfer_bonus(
        self,
        user: Dict[str, Any],
        matched_skills: List[Dict[str, Any]],
        user_skills_map: Dict[str, Dict[str, Any]],
        skills_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate transfer bonus for users with relevant tech under different L3.
        
        Transfer Bonus Logic:
        - If query matched an L3 skill AND the user has a relevant L4 technology
          under a DIFFERENT L3 parent, give them partial credit
        - This recognizes technology competence even in different contexts
        
        Example:
            Query matched: "Serverless Architecture (L3) > AWS (L4)"
            User has: "Cloud Security (L3) > AWS (L4)"
            → User gets transfer bonus for AWS experience
        
        Returns:
            Dictionary with 'bonus' (float) and 'details' (List[Dict])
        """
        transfer_count = 0
        transfer_details = []
        
        # Get L3 skills from matched results
        matched_l3_skills = [s for s in matched_skills if s['level'] == 3]
        
        for matched_l3 in matched_l3_skills:
            matched_l3_id = matched_l3['skill_id']
            
            # Skip if user directly has this L3 skill (no bonus needed)
            if matched_l3_id in user_skills_map:
                continue
            
            # Get L4 children of this matched L3 from skills_lookup
            l4_children = self._get_l4_children(matched_l3_id, skills_lookup)
            
            # Check if user has any of these L4 technologies under a DIFFERENT L3
            for l4_child_id in l4_children:
                if l4_child_id in user_skills_map:
                    # User has this technology
                    user_skill = user_skills_map[l4_child_id]
                    user_l3_parents = user_skill.get('parent_ids', [])
                    
                    # Check if it's under a DIFFERENT L3 (not the matched one)
                    # Find the L3 parent (parent_ids go from immediate parent to root)
                    user_l3_parent = None
                    for parent_id in user_l3_parents:
                        parent_skill = skills_lookup.get(parent_id, {})
                        if parent_skill.get('level') == 3:
                            user_l3_parent = parent_id
                            break
                    
                    # If user has this tech under a different L3, give transfer credit
                    if user_l3_parent and user_l3_parent != matched_l3_id:
                        transfer_count += 1
                        
                        # Track details for modal
                        user_l3_parent_data = skills_lookup.get(user_l3_parent, {})
                        transfer_details.append({
                            'source_skill_id': l4_child_id,
                            'source_skill_title': user_skill.get('title', ''),
                            'source_parent_title': user_l3_parent_data.get('title', 'Unknown'),
                            'matched_skill_id': l4_child_id,
                            'matched_skill_title': user_skill.get('title', ''),
                            'matched_parent_title': matched_l3['title'],
                            'bonus_amount': self.transfer_bonus_per_tech
                        })
        
        # Calculate bonus (per tech, capped)
        bonus = min(
            transfer_count * self.transfer_bonus_per_tech,
            self.transfer_bonus_cap
        )
        
        return {
            'bonus': bonus,
            'details': transfer_details
        }
    
    def _get_l4_children(
        self,
        parent_id: str,
        skills_lookup: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Get all L4 (technology) children of a given skill.
        """
        l4_children = []
        
        for skill_id, skill_data in skills_lookup.items():
            if skill_data.get('level') == 4:
                parent = skill_data.get('parent_id')
                if parent == parent_id:
                    l4_children.append(skill_id)
        
        return l4_children
    
    def rank_users(
        self,
        users_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank users by normalized score (descending).
        Adds rank number to each user.
        
        Args:
            users_scores: List of user score dictionaries
            
        Returns:
            Sorted list with rank added
        """
        # Sort by normalized score (descending)
        sorted_users = sorted(
            users_scores,
            key=lambda x: x['normalized_score'],
            reverse=True
        )
        
        # Add rank
        for i, user in enumerate(sorted_users, 1):
            user['rank'] = i
        
        return sorted_users
    
    def generate_score_breakdown(
        self,
        score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate detailed score breakdown for modal display.
        Shows top skills representing 80% of total score.
        
        Args:
            score_data: Full score data from calculate_user_score
            
        Returns:
            Dictionary with formatted breakdown for frontend
        """
        matched_skills_detail = score_data.get('matched_skills_detail', [])
        raw_score = score_data.get('raw_score', 0.0)
        normalized_score = score_data.get('normalized_score', 0.0)
        transfer_bonus = score_data.get('transfer_bonus', 0.0)
        transfer_bonus_details = score_data.get('transfer_bonus_details', [])
        
        # Sort skills by contribution (descending)
        sorted_skills = sorted(
            matched_skills_detail,
            key=lambda x: x.get('skill_score', 0),
            reverse=True
        )
        
        # Calculate cumulative contribution to find 80% threshold
        total_skill_score = sum(s.get('skill_score', 0) for s in sorted_skills)
        threshold = total_skill_score * 0.8
        cumulative = 0.0
        top_contributors = []
        
        for skill in sorted_skills:
            skill_score = skill.get('skill_score', 0)
            cumulative += skill_score
            
            # Calculate percentage of total score
            percentage = (skill_score / raw_score * 100) if raw_score > 0 else 0
            
            top_contributors.append({
                'skill_id': skill.get('skill_id'),
                'title': skill.get('title'),
                'level': skill.get('level'),
                'rating': skill.get('rating'),
                'similarity': skill.get('similarity'),
                'points_contributed': round(skill_score, 2),
                'percentage_of_total': round(percentage, 1),
                'match_type': skill.get('match_type', 'direct')
            })
            
            # Stop when we've reached 80% (but ensure at least 3 skills if available)
            if cumulative >= threshold and len(top_contributors) >= 3:
                break
        
        # Determine score interpretation
        if normalized_score >= 80:
            interpretation = "Excellent Match"
        elif normalized_score >= 60:
            interpretation = "Strong Match"
        elif normalized_score >= 40:
            interpretation = "Good Match"
        elif normalized_score >= 20:
            interpretation = "Fair Match"
        else:
            interpretation = "Weak Match"
        
        return {
            'raw_score': round(raw_score, 2),
            'normalized_score': round(normalized_score, 2),
            'total_matched_skills': len(matched_skills_detail),
            'skill_contributions': top_contributors,
            'transfer_bonus_total': round(transfer_bonus, 2),
            'transfer_bonus_details': transfer_bonus_details,
            'score_interpretation': interpretation
        }


# Singleton instance
_scoring_service: ScoringService = None


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
