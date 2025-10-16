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
    points_contributed: float  # How many points this skill added to total score
    percentage_of_total: float  # What % of user's total score this represents
    match_type: str  # 'direct' or other types
    parent_titles: List[str] = []  # Skill hierarchy for display


class TransferBonusDetail(BaseModel):
    """Model for transfer bonus details."""
    source_skill_id: str
    source_skill_title: str
    source_parent_title: str  # The L3 parent the user has this under
    matched_skill_id: str
    matched_skill_title: str
    matched_parent_title: str  # The L3 parent from the query match
    bonus_amount: float


class ScoreBreakdown(BaseModel):
    """Model for detailed score breakdown for a user."""
    raw_score: float
    normalized_score: float
    total_matched_skills: int
    skill_contributions: List[SkillContribution]  # Top contributors (80% of score)
    transfer_bonus_total: float
    transfer_bonus_details: List[TransferBonusDetail] = []
    score_interpretation: str  # e.g., "Excellent Match", "Strong Match"


class UserResult(BaseModel):
    """Model for a user search result."""
    email: str
    name: str
    rank: int
    score: float  # Normalized 0-100
    matched_skills: List[MatchedSkill]
    transfer_bonus: float
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
