"""
Scoring Algorithm Configuration

This module defines the configurable parameters for the two-dimensional
scoring algorithm used to rank users based on skill matches.

The scoring algorithm evaluates users across two dimensions:
1. COVERAGE: How many relevant skills the user has (weighted by similarity)
2. EXPERTISE: The proficiency level of the user's matched skills

Configuration values can be adjusted here and will be used for a future
score tuning interface where users can adjust weights via UI sliders.
"""

from typing import Dict


class ScoringAlgorithmConfig:
    """Configuration for the two-dimensional scoring algorithm."""
    
    # ==========================================================================
    # Rating Multipliers - How much each proficiency level is weighted
    # ==========================================================================
    # These multipliers are applied to matched skills based on user's self-assessed rating
    # Higher multipliers reward expertise in relevant skills
    
    RATING_MULTIPLIER_BEGINNER: float = 1.0
    """Beginner level (1) - baseline multiplier"""
    
    RATING_MULTIPLIER_INTERMEDIATE: float = 3.0
    """Intermediate level (2) - 3x beginner"""
    
    RATING_MULTIPLIER_ADVANCED: float = 6.0
    """Advanced level (3) - 6x beginner, recognizes significant expertise"""
    
    @classmethod
    def get_rating_multipliers(cls) -> Dict[int, float]:
        """Get rating multipliers as a dictionary."""
        return {
            1: cls.RATING_MULTIPLIER_BEGINNER,
            2: cls.RATING_MULTIPLIER_INTERMEDIATE,
            3: cls.RATING_MULTIPLIER_ADVANCED,
        }
    
    # ==========================================================================
    # Similarity Weighting - How similarity scores are weighted
    # ==========================================================================
    # Controls the exponential weighting of similarity scores
    # Higher values emphasize high-similarity matches more strongly
    
    SIMILARITY_EXPONENT: float = 2.0
    """
    Exponent applied to similarity scores (similarity^exponent).
    
    Examples with exponent=2.0:
    - 80% similarity: 0.80² = 0.64 contribution
    - 50% similarity: 0.50² = 0.25 contribution  
    - 30% similarity: 0.30² = 0.09 contribution
    
    This creates natural relevancy weighting where high-similarity skills
    dominate without completely excluding lower-similarity matches.
    """
    
    # ==========================================================================
    # Coverage Calculation - Maximum possible coverage baseline
    # ==========================================================================
    
    COVERAGE_MAX_PERCENTILE: float = 1.0
    """
    Percentile of matched skills to use for maximum coverage calculation.
    
    1.0 = Use all matched skills (100th percentile)
    0.5 = Use top 50% of matched skills by similarity
    
    This determines the denominator when calculating coverage percentage.
    Default: 1.0 (all skills count toward max coverage)
    """
    
    # ==========================================================================
    # Expertise Labels - Human-readable expertise descriptions
    # ==========================================================================
    
    EXPERTISE_LABELS = {
        (1.0, 1.5): "Beginner",
        (1.5, 2.5): "Early Career",
        (2.5, 4.0): "Intermediate",
        (4.0, 5.0): "Advanced",
        (5.0, 6.1): "Expert",
    }
    """
    Labels for expertise multiplier ranges.
    Used to display human-readable expertise levels in the UI.
    
    Range format: (min_inclusive, max_exclusive)
    """
    
    @classmethod
    def get_expertise_label(cls, expertise_multiplier: float) -> str:
        """
        Get human-readable label for an expertise multiplier value.
        
        Args:
            expertise_multiplier: The calculated expertise multiplier (1.0-6.0)
            
        Returns:
            Human-readable label (e.g., "Advanced", "Expert")
        """
        for (min_val, max_val), label in cls.EXPERTISE_LABELS.items():
            if min_val <= expertise_multiplier < max_val:
                return label
        return "Expert"  # Fallback for values >= 6.0
    
    # ==========================================================================
    # Display Scaling - For UI presentation
    # ==========================================================================
    
    SCORE_DISPLAY_SCALE: float = 100.0
    """
    Scale factor for displaying raw scores as relative percentages.
    
    The top user's raw score is normalized to this value, and all other
    users' scores are scaled proportionally. This makes scores easier to
    interpret at a glance while preserving relative rankings.
    
    Default: 100.0 (display as 0-100 scale with top user at 100)
    """
    
    # ==========================================================================
    # Future Configuration Placeholders
    # ==========================================================================
    # These are reserved for future score tuning features
    
    # COVERAGE_WEIGHT: float = 1.0
    # """Weight applied to coverage dimension (for multi-dimensional tuning)"""
    # 
    # EXPERTISE_WEIGHT: float = 1.0
    # """Weight applied to expertise dimension (for multi-dimensional tuning)"""
    #
    # MIN_SIMILARITY_THRESHOLD: float = 0.0
    # """Minimum similarity to include a skill in scoring (0.0 = include all)"""


# Create singleton instance for easy import
scoring_config = ScoringAlgorithmConfig()
