"""
User Repository - Data access layer for user data.
Implements repository pattern to allow future DB swaps (DynamoDB, PostgreSQL, etc.)
"""

import json
import os
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class UserRepository(ABC):
    """
    Abstract base class for user data access.
    This interface remains consistent even when swapping implementations.
    """
    
    @abstractmethod
    def load_data(self) -> None:
        """Load data from source."""
        pass
    
    @abstractmethod
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get specific user by email."""
        pass
    
    @abstractmethod
    def get_users_by_skill_id(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get users who have a specific skill."""
        pass
    
    @abstractmethod
    def get_users_count(self) -> int:
        """Get total user count."""
        pass
    
    @abstractmethod
    def get_skills_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Get skills lookup table."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data (last ingested, counts, etc.)."""
        pass


class InMemoryUserRepository(UserRepository):
    """
    In-memory implementation loading from user_db.json.
    Optimized for fast lookups during search operations.
    
    Data Structure:
    {
        "metadata": {...},
        "skills_lookup": {skill_id: skill_details},
        "users": [user_objects],
        "indexes": {
            "by_email": {email: user_index},
            "by_l3_skill": {l3_skill_id: [user_indexes]},
            "by_l4_skill": {l4_skill_id: [user_indexes]}
        }
    }
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.data = None
        self.users = []
        self.skills_lookup = {}
        self.metadata = {}
        self.indexes = {}
    
    def load_data(self) -> None:
        """Load user_db.json into memory and build indexes."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"User database not found at {self.db_path}. "
                f"Please run the ingestion script first: python scripts/ingest_users.py"
            )
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.metadata = self.data.get('metadata', {})
        self.skills_lookup = self.data.get('skills_lookup', {})
        self.users = self.data.get('users', [])
        self.indexes = self.data.get('indexes', {})
        
        print(f"✅ Loaded {len(self.users)} users and {len(self.skills_lookup)} skills from {self.db_path}")
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        return self.users
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get specific user by email."""
        email_index = self.indexes.get('by_email', {})
        user_idx = email_index.get(email)
        
        if user_idx is not None and 0 <= user_idx < len(self.users):
            return self.users[user_idx]
        return None
    
    def get_users_by_skill_id(self, skill_id: str) -> List[Dict[str, Any]]:
        """
        Get users who have a specific skill.
        Checks both L3 and L4 indexes for efficiency.
        """
        users = []
        
        # Check L3 index
        l3_index = self.indexes.get('by_l3_skill', {})
        if skill_id in l3_index:
            for user_idx in l3_index[skill_id]:
                if 0 <= user_idx < len(self.users):
                    users.append(self.users[user_idx])
        
        # Check L4 index
        l4_index = self.indexes.get('by_l4_skill', {})
        if skill_id in l4_index:
            for user_idx in l4_index[skill_id]:
                if 0 <= user_idx < len(self.users):
                    user = self.users[user_idx]
                    if user not in users:  # Avoid duplicates
                        users.append(user)
        
        return users
    
    def get_users_count(self) -> int:
        """Get total user count."""
        return len(self.users)
    
    def get_skills_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Get skills lookup table."""
        return self.skills_lookup
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data."""
        return self.metadata


# Singleton instance (initialized in main.py on startup)
_repository_instance: Optional[UserRepository] = None


def init_repository(db_path: str) -> UserRepository:
    """Initialize the global repository instance."""
    global _repository_instance
    _repository_instance = InMemoryUserRepository(db_path)
    _repository_instance.load_data()
    return _repository_instance


def get_repository() -> UserRepository:
    """Get the global repository instance."""
    if _repository_instance is None:
        raise RuntimeError("Repository not initialized. Call init_repository() first.")
    return _repository_instance
