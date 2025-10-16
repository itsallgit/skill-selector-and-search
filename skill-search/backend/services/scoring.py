"""
Scoring Service - Two-Dimensional User Ranking Algorithm

This module implements a two-dimensional scoring system that evaluates users based on:
1. COVERAGE: How many relevant skills the user possesses (weighted by similarity)
2. EXPERTISE: The proficiency level of the user's matched skills (rating-based)

The algorithm trusts the vector search's similarity scores and uses them to naturally
weight skill importance without arbitrary thresholds or complex normalization.
"""

from typing import List, Dict, Any
from scoring_algorithm import scoring_config
import logging

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring and ranking users using two-dimensional algorithm."""
    
    def __init__(self):
        """Initialize scoring service with configured parameters."""
        self.rating_multipliers = scoring_config.get_rating_multipliers()
        self.similarity_exponent = scoring_config.SIMILARITY_EXPONENT
        logger.info(f"Scoring service initialized with rating multipliers: {self.rating_multipliers}")
    
    def calculate_user_score(
        self,
        user: Dict[str, Any],
        matched_skills: List[Dict[str, Any]],
        skills_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate two-dimensional score for a user against matched skills.
        
        Args:
            user: User object with skills data
            matched_skills: List of skills from vector search with similarity scores
            skills_lookup: Full skills lookup table for hierarchy info
            
        Returns:
            Dictionary with comprehensive score breakdown
        """
        user_email = user.get('userEmail', user.get('email', 'unknown'))
        logger.debug(f"Calculating score for user: {user_email}")
        
        # Build user skill lookups for efficient matching
        user_skills_map = self._build_user_skills_map(user)
        logger.debug(f"User {user_email} has {len(user_skills_map)} skills")
        
        # Calculate maximum possible coverage
        max_possible_coverage = self._calculate_max_coverage(matched_skills)
        
        # Initialize scoring variables
        coverage_score = 0.0
        expertise_weighted_sum = 0.0
        matched_skills_detail = []
        
        # Score each matched skill
        for matched_skill in matched_skills:
            skill_id = matched_skill['skill_id']
            similarity = matched_skill['similarity']
            
            # Check if user has this skill
            if skill_id in user_skills_map:
                user_skill = user_skills_map[skill_id]
                rating = user_skill['rating']
                level = user_skill.get('level', matched_skill.get('level', 0))
                title = user_skill.get('title', matched_skill.get('title', ''))
                
                # Calculate relevancy weight (similarity squared)
                relevancy_weight = similarity ** self.similarity_exponent
                
                # Add to coverage
                coverage_score += relevancy_weight
                
                # Add to expertise (coverage weighted by rating)
                rating_multiplier = self.rating_multipliers.get(rating, 1.0)
                expertise_contribution = relevancy_weight * rating_multiplier
                expertise_weighted_sum += expertise_contribution
                
                # Get parent titles for hierarchy display
                parent_titles = user_skill.get('parent_ids', [])
                parent_title_list = []
                for parent_id in parent_titles:
                    parent_skill = skills_lookup.get(parent_id, {})
                    if parent_skill.get('title'):
                        parent_title_list.append(parent_skill['title'])
                
                # Track details for modal display
                matched_skills_detail.append({
                    'skill_id': skill_id,
                    'title': title,
                    'level': level,
                    'rating': rating,
                    'similarity': similarity,
                    'relevancy_weight': relevancy_weight,
                    'coverage_contribution': relevancy_weight,
                    'expertise_contribution': expertise_contribution,
                    'rating_multiplier': rating_multiplier,
                    'parent_titles': parent_title_list
                })
        
        # Calculate coverage percentage
        coverage_percentage = 0.0
        if max_possible_coverage > 0:
            coverage_percentage = (coverage_score / max_possible_coverage) * 100
        
        # Calculate expertise multiplier (weighted average)
        expertise_multiplier = 1.0  # Default to beginner if no skills
        if coverage_score > 0:
            expertise_multiplier = expertise_weighted_sum / coverage_score
        
        # Get human-readable expertise label
        expertise_label = scoring_config.get_expertise_label(expertise_multiplier)
        
        # Calculate raw score (coverage x expertise)
        raw_score = coverage_score * expertise_multiplier
        
        # Sort skills by coverage contribution (descending) for display
        matched_skills_detail.sort(key=lambda x: x['coverage_contribution'], reverse=True)
        
        return {
            'coverage_score': coverage_score,
            'coverage_percentage': round(coverage_percentage, 2),
            'expertise_multiplier': round(expertise_multiplier, 2),
            'expertise_label': expertise_label,
            'raw_score': round(raw_score, 4),
            'matched_skills_detail': matched_skills_detail,
            'total_matched_skills': len(matched_skills_detail)
        }
    
    def _build_user_skills_map(self, user: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Build efficient lookup map of user's skills."""
        skills_map = {}
        
        # Handle both 'skills' (processed) and 'selectedSkills' (raw) formats
        user_skills = user.get('skills', user.get('selectedSkills', []))
        
        for skill in user_skills:
            skill_id = skill.get('skill_id')
            if skill_id:
                skills_map[skill_id] = {
                    'rating': skill.get('rating', 1),
                    'level': skill.get('skill_level', 0),
                    'title': skill.get('skill_title', ''),
                    'parent_ids': skill.get('parent_ids', [])
                }
        
        return skills_map
    
    def _calculate_max_coverage(self, matched_skills: List[Dict[str, Any]]) -> float:
        """Calculate maximum possible coverage score."""
        max_coverage = 0.0
        
        for skill in matched_skills:
            similarity = skill.get('similarity', 0.0)
            relevancy_weight = similarity ** self.similarity_exponent
            max_coverage += relevancy_weight
        
        return max_coverage
    
    def rank_users(
        self,
        users_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank users by raw score (descending) and add display scores."""
        if not users_scores:
            return []
        
        # Sort by raw score (descending)
        sorted_users = sorted(
            users_scores,
            key=lambda x: x['raw_score'],
            reverse=True
        )
        
        # Find top score for scaling
        top_score = sorted_users[0]['raw_score'] if sorted_users else 1.0
        
        # Add rank and display score
        for i, user in enumerate(sorted_users, 1):
            user['rank'] = i
            
            # Calculate display score (scaled to 100 for top user)
            if top_score > 0:
                display_score = (user['raw_score'] / top_score) * scoring_config.SCORE_DISPLAY_SCALE
            else:
                display_score = 0.0
            
            user['display_score'] = round(display_score, 2)
        
        return sorted_users
    
    def generate_score_breakdown(
        self,
        score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed score breakdown for modal display."""
        matched_skills_detail = score_data.get('matched_skills_detail', [])
        coverage_score = score_data.get('coverage_score', 0.0)
        coverage_percentage = score_data.get('coverage_percentage', 0.0)
        expertise_multiplier = score_data.get('expertise_multiplier', 1.0)
        expertise_label = score_data.get('expertise_label', 'Beginner')
        raw_score = score_data.get('raw_score', 0.0)
        
        # Build detailed skill contributions list
        skill_contributions = []
        for skill in matched_skills_detail:
            coverage_contrib = skill.get('coverage_contribution', 0)
            coverage_pct = (coverage_contrib / coverage_score * 100) if coverage_score > 0 else 0
            
            skill_contributions.append({
                'skill_id': skill.get('skill_id'),
                'title': skill.get('title'),
                'level': skill.get('level'),
                'rating': skill.get('rating'),
                'similarity': skill.get('similarity'),
                'relevancy_weight': skill.get('relevancy_weight'),
                'coverage_contribution': round(coverage_contrib, 4),
                'coverage_percentage': round(coverage_pct, 1),
                'expertise_contribution': round(skill.get('expertise_contribution', 0), 4),
                'rating_multiplier': skill.get('rating_multiplier'),
                'parent_titles': skill.get('parent_titles', [])
            })
        
        return {
            'coverage_score': round(coverage_score, 4),
            'coverage_percentage': round(coverage_percentage, 2),
            'expertise_multiplier': round(expertise_multiplier, 2),
            'expertise_label': expertise_label,
            'raw_score': round(raw_score, 4),
            'total_matched_skills': len(matched_skills_detail),
            'skill_contributions': skill_contributions
        }


# Singleton instance
_scoring_service: ScoringService = None


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
