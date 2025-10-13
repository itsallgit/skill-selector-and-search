"""
User Repository - Data access layer for user data.
Implements repository pattern to allow future DB swaps (DynamoDB, PostgreSQL, etc.)
"""

import json
import os
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


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
        raw_users = self.data.get('users', [])
        self.indexes = self.data.get('indexes', {})
        
        # Transform users from compact format to expanded format
        self.users = self._expand_users(raw_users)
        
        logger.info(f"✅ Loaded {len(self.users)} users and {len(self.skills_lookup)} skills from {self.db_path}")
    
    def _expand_users(self, raw_users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform users from compact storage format to expanded format expected by the application.
        
        Compact format (from S3):
        {
            "userEmail": "user@example.com",
            "selectedSkills": [
                {
                    "l1Id": "L1ABC",
                    "l2Id": "L2DEF",
                    "l3Id": "L3GHI",
                    "l4Ids": ["L4JKL", "L4MNO"],
                    "rating": 2
                }
            ]
        }
        
        Expanded format (for application):
        {
            "email": "user@example.com",
            "name": "user",
            "skills": [
                {
                    "skill_id": "L3GHI",
                    "skill_title": "Skill Title",
                    "skill_level": 3,
                    "rating": 2,
                    "parent_ids": ["L1ABC", "L2DEF"],
                    ...
                },
                {
                    "skill_id": "L4JKL",
                    "skill_title": "Tech Title",
                    "skill_level": 4,
                    "rating": 2,
                    "parent_ids": ["L1ABC", "L2DEF", "L3GHI"],
                    ...
                }
            ]
        }
        """
        expanded_users = []
        
        # We need to load skills master data to get titles
        # Try to load from ../data/skills-master.json
        skills_master = self._load_skills_master()
        
        for raw_user in raw_users:
            user_email = raw_user.get('userEmail', '')
            user_name = user_email.split('@')[0] if user_email else 'Unknown'
            
            expanded_skills = []
            
            for selected_skill in raw_user.get('selectedSkills', []):
                l1_id = selected_skill.get('l1Id')
                l2_id = selected_skill.get('l2Id')
                l3_id = selected_skill.get('l3Id')
                l4_ids = selected_skill.get('l4Ids', [])
                rating = selected_skill.get('rating', 1)
                
                # Add L3 skill
                if l3_id:
                    l3_skill = {
                        'skill_id': l3_id,
                        'skill_title': skills_master.get(l3_id, {}).get('title', l3_id),
                        'skill_level': 3,
                        'rating': rating,
                        'parent_ids': [l1_id, l2_id],
                        'parent_titles': [
                            skills_master.get(l1_id, {}).get('title', ''),
                            skills_master.get(l2_id, {}).get('title', '')
                        ]
                    }
                    expanded_skills.append(l3_skill)
                
                # Add L4 skills
                for l4_id in l4_ids:
                    l4_skill = {
                        'skill_id': l4_id,
                        'skill_title': skills_master.get(l4_id, {}).get('title', l4_id),
                        'skill_level': 4,
                        'rating': rating,
                        'parent_ids': [l1_id, l2_id, l3_id],
                        'parent_titles': [
                            skills_master.get(l1_id, {}).get('title', ''),
                            skills_master.get(l2_id, {}).get('title', ''),
                            skills_master.get(l3_id, {}).get('title', '')
                        ]
                    }
                    expanded_skills.append(l4_skill)
            
            expanded_user = {
                'email': user_email,
                'name': user_name,
                'skills': expanded_skills,
                'userEmail': user_email,  # Keep for backwards compatibility
                'selectedSkills': raw_user.get('selectedSkills', [])  # Keep original
            }
            
            expanded_users.append(expanded_user)
        
        logger.info(f"Expanded {len(expanded_users)} users with skill details")
        return expanded_users
    
    def _load_skills_master(self) -> Dict[str, Dict[str, Any]]:
        """Load skills master data for skill titles."""
        # The db_path is 'data/user_db.json' which resolves to /app/data/user_db.json
        # But /data is mounted to ../data (project root data folder)
        # So we need to check multiple possible locations
        
        possible_paths = [
            # If running in Docker with /data mount
            '/data/skills-master.json',
            # If running locally from backend directory
            os.path.join(os.path.dirname(self.db_path), '..', '..', 'data', 'skills-master.json'),
            # Relative to backend directory
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'skills-master.json'),
        ]
        
        for skills_master_path in possible_paths:
            skills_master_path = os.path.normpath(skills_master_path)
            
            if os.path.exists(skills_master_path):
                try:
                    with open(skills_master_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Flatten the nested hierarchy into a lookup dict
                        lookup = self._flatten_skills_hierarchy(data)
                        logger.info(f"Loaded {len(lookup)} skills from {skills_master_path}")
                        return lookup
                except Exception as e:
                    logger.warning(f"Failed to load skills master from {skills_master_path}: {e}")
            else:
                logger.debug(f"Skills master not found at {skills_master_path}")
        
        logger.warning("Could not find skills-master.json in any expected location")
        return {}
    
    def _flatten_skills_hierarchy(self, skills_array: List[Dict[str, Any]], parent_ids: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Recursively flatten nested skills hierarchy into a flat lookup dict.
        
        Input (nested):
        [
            {
                "id": "L1ABC",
                "title": "L1 Title",
                "skills": [
                    {"id": "L2DEF", "title": "L2 Title", "skills": [...]}
                ]
            }
        ]
        
        Output (flat):
        {
            "L1ABC": {"id": "L1ABC", "title": "L1 Title", "level": 1, "parent_ids": []},
            "L2DEF": {"id": "L2DEF", "title": "L2 Title", "level": 2, "parent_ids": ["L1ABC"]},
            ...
        }
        """
        if parent_ids is None:
            parent_ids = []
        
        lookup = {}
        
        for skill in skills_array:
            skill_id = skill.get('id')
            if not skill_id:
                continue
            
            # Add this skill to lookup
            lookup[skill_id] = {
                'id': skill_id,
                'title': skill.get('title', skill_id),
                'level': skill.get('level', len(parent_ids) + 1),
                'parent_ids': parent_ids.copy()
            }
            
            # Recursively process child skills
            child_skills = skill.get('skills', [])
            if child_skills:
                child_parent_ids = parent_ids + [skill_id]
                child_lookup = self._flatten_skills_hierarchy(child_skills, child_parent_ids)
                lookup.update(child_lookup)
        
        return lookup
    
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
