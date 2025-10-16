"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SearchRequest(BaseModel):
    """Request model for user search endpoint."""
    query: str = Field(..., description="Natural language search query")
    top_k_skills: Optional[int] = Field(10, description="Number of skills to retrieve from vector search")
    top_n_users: Optional[int] = Field(5, description="Number of top users to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "AWS Lambda and serverless architecture",
                "top_k_skills": 10,
                "top_n_users": 5
            }
        }


class MatchedSkill(BaseModel):
    """Model for a matched skill from vector search."""
    skill_id: str
    title: str
    level: int
    parent_titles: List[str] = []
    similarity: float
    color: str
    rating: Optional[int] = None  # User's rating for this skill (1-3)


class SkillContribution(BaseModel):
    """Model for individual skill contribution to user score."""
    skill_id: str
    title: str
    level: int
    rating: int
    similarity: float
    relevancy_weight: float  # similarity^2
    coverage_contribution: float  # Contribution to coverage score
    coverage_percentage: float  # % of total coverage this skill represents
    expertise_contribution: float  # relevancy_weight * rating_multiplier
    rating_multiplier: float  # 1.0, 3.0, or 6.0 based on rating
    parent_titles: List[str] = []  # Skill hierarchy for display


class ScoreBreakdown(BaseModel):
    """Model for detailed score breakdown for a user."""
    coverage_score: float  # Raw coverage value (sum of similarity^2)
    coverage_percentage: float  # Coverage as % of maximum possible (0-100)
    expertise_multiplier: float  # Weighted average rating multiplier (1.0-6.0)
    expertise_label: str  # Human-readable: Beginner, Early Career, Intermediate, Advanced, Expert
    raw_score: float  # coverage_score * expertise_multiplier
    display_score: Optional[float] = None  # Scaled score (top user = 100), added after ranking
    total_matched_skills: int
    skill_contributions: List[SkillContribution]  # Detailed per-skill breakdown


class UserResult(BaseModel):
    """Model for a user search result."""
    email: str
    name: str
    rank: int
    coverage_score: float  # Raw coverage value
    coverage_percentage: float  # Coverage as % of maximum (0-100)
    expertise_multiplier: float  # Weighted average rating (1.0-6.0)
    expertise_label: str  # Human-readable expertise level
    raw_score: float  # coverage * expertise (for sorting)
    display_score: float  # Scaled to top user = 100
    matched_skills: List[MatchedSkill]
    score_breakdown: Optional[ScoreBreakdown] = None  # Detailed breakdown for modal


class ScoreBucket(BaseModel):
    """Model for a score bucket/bracket."""
    name: str
    min_score: float
    max_score: float
    count: int
    users: List[UserResult] = []


class SearchResponse(BaseModel):
    """Response model for user search endpoint."""
    matched_skills: List[MatchedSkill]
    top_users: List[UserResult]
    buckets: List[ScoreBucket]


class SkillDetail(BaseModel):
    """Model for skill details in user profile."""
    skill_id: str
    title: str
    rating: int
    parent_titles: List[str] = []


class UserDetail(BaseModel):
    """Model for detailed user profile."""
    email: str
    name: str
    total_skills: int
    l1_skills: List[SkillDetail]
    l2_skills: List[SkillDetail]
    l3_skills: List[SkillDetail]
    l4_skills: List[SkillDetail]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    user_count: int


class StatsResponse(BaseModel):
    """Statistics response."""
    total_users: int
    total_skills: int
    skills_by_level: Dict[int, int]
    skills_by_rating: Dict[int, int]
    config: Dict[str, Any]
