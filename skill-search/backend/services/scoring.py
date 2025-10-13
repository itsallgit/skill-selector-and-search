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
        transfer_bonus_amount = self._calculate_transfer_bonus(
            user,
            matched_skills,
            user_skills_map,
            skills_lookup
        )
        
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
            'has_transfer_bonus': transfer_bonus_amount > 0
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
    ) -> float:
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
            Transfer bonus amount (capped)
        """
        transfer_count = 0
        
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
        
        # Calculate bonus (per tech, capped)
        bonus = min(
            transfer_count * self.transfer_bonus_per_tech,
            self.transfer_bonus_cap
        )
        
        return bonus
    
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


# Singleton instance
_scoring_service: ScoringService = None


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
