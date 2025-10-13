"""
Configuration management for Skills Search backend.
Uses environment variables with sensible defaults.

AWS Profile Configuration Strategy:
- Single Account Setup: Set AWS_PROFILE and all tasks use it
- Multi-Account Setup: Override specific tasks (EMBEDDING_AWS_PROFILE, VECTOR_AWS_PROFILE, etc.)
- Task-specific profiles fall back to AWS_PROFILE if not specified
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Info
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # ============================================================================
    # AWS Configuration - Default (fallback for all tasks)
    # ============================================================================
    aws_profile: str = "default"
    aws_region: str = "ap-southeast-2"
    
    # ============================================================================
    # Task 1: Embedding Generation (AWS Bedrock)
    # Falls back to aws_profile/aws_region if not specified
    # ============================================================================
    embedding_aws_profile: Optional[str] = None
    embedding_aws_region: Optional[str] = None
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    embedding_dim: int = 1024
    
    # ============================================================================
    # Task 2: Vector Index Querying (AWS S3 Vectors)
    # Falls back to aws_profile/aws_region if not specified
    # ============================================================================
    vector_aws_profile: Optional[str] = None
    vector_aws_region: Optional[str] = None
    vector_bucket: str = Field(
        default="",
        description="S3 Vector bucket containing skill embeddings (e.g., 'skills-vectors-XXXXXXXXXX')"
    )
    vector_index: str = "skills-index"
    
    # ============================================================================
    # Task 3: Data Ingestion (AWS S3 Read)
    # Falls back to aws_profile/aws_region if not specified
    # ============================================================================
    ingestion_aws_profile: Optional[str] = None
    ingestion_aws_region: Optional[str] = None
    ingestion_bucket: str = Field(
        default="",
        description="S3 bucket containing user data (e.g., 'skills-selector-XXXXXXXXXX')"
    )
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Data Paths
    user_db_path: str = "data/user_db.json"
    
    # Search Configuration
    top_k_skills: int = 20  # Number of skills to retrieve from vector search
    min_similarity: float = 0.35  # Minimum similarity threshold
    
    # Scoring Weights (configurable)
    level_weight_l1: float = 0.1
    level_weight_l2: float = 0.2
    level_weight_l3: float = 0.5
    level_weight_l4: float = 0.3
    
    # Rating Multipliers (exponential)
    rating_multiplier_1: float = 1.0  # Beginner
    rating_multiplier_2: float = 2.0  # Intermediate
    rating_multiplier_3: float = 4.0  # Advanced
    
    # Transfer Bonus
    transfer_bonus_per_tech: float = 0.02
    transfer_bonus_cap: float = 0.15
    
    # Score Buckets (for display)
    excellent_min_score: int = 80
    strong_min_score: int = 60
    good_min_score: int = 40
    
    # Display Configuration
    top_users_count: int = 5
    users_per_page: int = 10
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'  # Allow extra fields in .env that aren't defined in Settings
    )
    
    # ============================================================================
    # Helper Methods - Get effective profile/region with fallback logic
    # ============================================================================
    
    def get_embedding_profile(self) -> str:
        """Get AWS profile for Bedrock embedding generation."""
        return self.embedding_aws_profile or self.aws_profile
    
    def get_embedding_region(self) -> str:
        """Get AWS region for Bedrock embedding generation."""
        return self.embedding_aws_region or self.aws_region
    
    def get_vector_profile(self) -> str:
        """Get AWS profile for S3 Vector index querying."""
        return self.vector_aws_profile or self.aws_profile
    
    def get_vector_region(self) -> str:
        """Get AWS region for S3 Vector index querying."""
        return self.vector_aws_region or self.aws_region
    
    def get_ingestion_profile(self) -> str:
        """Get AWS profile for S3 data ingestion."""
        return self.ingestion_aws_profile or self.aws_profile
    
    def get_ingestion_region(self) -> str:
        """Get AWS region for S3 data ingestion."""
        return self.ingestion_aws_region or self.aws_region


# Global settings instance
settings = Settings()
