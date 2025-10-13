"""
API Routes - REST endpoints for the Skills Search application.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging
import json

from api.models import (
    SearchRequest,
    SearchResponse,
    UserResult,
    MatchedSkill,
    ScoreBucket,
    UserDetail,
    HealthResponse,
    StatsResponse
)
from services.vector_search import get_vector_search_service
from services.user_repository import get_repository
from services.scoring import get_scoring_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/search", response_model=SearchResponse)
async def search_skills(request: SearchRequest):
    """
    Search for users by natural language skill query.
    
    Process:
    1. Generate embedding for query
    2. Search vector index for matching skills
    3. Find users with those skills
    4. Score and rank users
    5. Organize into score buckets
    
    Returns:
        SearchResponse with matched skills, top users, and score buckets
    """
    try:
        # Get services
        vector_service = get_vector_search_service()
        user_repo = get_repository()
        scoring_service = get_scoring_service()
        
        # Step 1: Vector search for matching skills
        logger.info(f"Searching for query: '{request.query}' (top_k={request.top_k_skills})")
        matched_skills_raw = vector_service.search_skills(
            query_text=request.query,
            top_k=request.top_k_skills
        )
        
        if not matched_skills_raw:
            logger.warning("No matching skills found")
            return SearchResponse(
                matched_skills=[],
                top_users=[],
                buckets=[]
            )
        
        # Convert to MatchedSkill models
        matched_skills = [
            MatchedSkill(
                skill_id=s['skill_id'],
                title=s['title'],
                level=s['level'],
                parent_titles=s.get('ancestor_ids', []),  # Use ancestor_ids from metadata
                similarity=s['similarity'],
                color=s.get('emoji', '🔵')  # Use emoji as color indicator
            )
            for s in matched_skills_raw
        ]
        
        logger.info(f"Found {len(matched_skills)} matching skills")
        logger.info(f"Matched skill IDs: {[s.skill_id for s in matched_skills[:5]]}")  # Log first 5
        
        # Step 2: Find all users who have any of these skills
        all_users = user_repo.get_all_users()
        logger.info(f"Total users in database: {len(all_users)}")
        
        # Log the structure of the first user to understand the data format
        if all_users:
            first_user = all_users[0]
            logger.info(f"Sample user structure - keys: {list(first_user.keys())}")
            logger.info(f"Sample user data: {json.dumps(first_user, indent=2)[:500]}")  # First 500 chars
        
        matched_skill_ids = {s.skill_id for s in matched_skills}
        
        # Build skills lookup for hierarchy info
        skills_lookup = _build_skills_lookup(all_users)
        
        # Step 3: Score users
        users_scores = []
        for user in all_users:
            # Check if user has any matched skills
            user_skill_ids = {skill.get('skill_id') for skill in user.get('skills', [])}
            logger.debug(f"Processing user, has {len(user_skill_ids)} skills")
            
            if not user_skill_ids.intersection(matched_skill_ids):
                # No matches, but check for transfer bonus eligibility
                logger.debug(f"User has no direct skill matches")
                pass  # Let scoring service handle transfer bonus
            
            # Calculate score
            score_data = scoring_service.calculate_user_score(
                user=user,
                matched_skills=[s.model_dump() for s in matched_skills],
                skills_lookup=skills_lookup
            )
            
            # Skip users with zero score
            if score_data['normalized_score'] == 0:
                logger.debug(f"Skipping user with zero score")
                continue
            
            # Get user email from either field name
            user_email = user.get('email', user.get('userEmail', 'unknown'))
            user_name = user.get('name', user_email.split('@')[0])  # Default name from email
            
            # Build matched skills for this user with parent titles
            user_matched_skills = []
            for detail in score_data['matched_skills_detail']:
                # Get parent titles from the user's skill data
                user_skill = next(
                    (s for s in user.get('skills', []) if s.get('skill_id') == detail['skill_id']),
                    None
                )
                parent_titles = user_skill.get('parent_titles', []) if user_skill else []
                
                user_matched_skills.append(
                    MatchedSkill(
                        skill_id=detail['skill_id'],
                        title=detail['title'],
                        level=detail['level'],
                        parent_titles=parent_titles,
                        similarity=detail['similarity'],
                        color='',  # Will use global match color
                        rating=detail.get('rating', 1)  # Include user's rating
                    )
                )
            
            logger.debug(f"Adding user {user_email} with score {score_data['normalized_score']}")
            
            users_scores.append({
                'email': user_email,
                'name': user_name,
                'score': score_data['normalized_score'],
                'normalized_score': score_data['normalized_score'],  # For rank_users function
                'raw_score': score_data['raw_score'],
                'matched_skills': user_matched_skills,
                'transfer_bonus': score_data['transfer_bonus'],
                'has_transfer_bonus': score_data['has_transfer_bonus']
            })
        
        if not users_scores:
            logger.warning(f"No users found with matching skills out of {len(all_users)} total users")
            logger.warning(f"Matched skill IDs were: {list(matched_skill_ids)[:10]}")  # Log first 10
            return SearchResponse(
                matched_skills=matched_skills,
                top_users=[],
                buckets=[]
            )
        
        # Step 4: Rank users
        ranked_users = scoring_service.rank_users(users_scores)
        logger.info(f"Ranked {len(ranked_users)} users")
        
        # Step 5: Get top N users
        top_users = [
            UserResult(
                email=u['email'],
                name=u['name'],
                rank=u['rank'],
                score=u['score'],
                matched_skills=u['matched_skills'],
                transfer_bonus=u['transfer_bonus']
            )
            for u in ranked_users[:request.top_n_users]
        ]
        
        # Step 6: Organize remaining users into score buckets
        buckets = _create_score_buckets(ranked_users[request.top_n_users:])
        
        return SearchResponse(
            matched_skills=matched_skills,
            top_users=top_users,
            buckets=buckets
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/api/users/{email}", response_model=UserDetail)
async def get_user_detail(email: str):
    """
    Get detailed information about a specific user.
    
    Returns:
        UserDetail with full skill breakdown
    """
    try:
        user_repo = get_repository()
        user = user_repo.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' not found"
            )
        
        # Organize skills by hierarchy level
        skills_by_level = {1: [], 2: [], 3: [], 4: []}
        for skill in user.get('skills', []):
            level = skill.get('skill_level', 0)
            if level in skills_by_level:
                skills_by_level[level].append({
                    'skill_id': skill.get('skill_id'),
                    'title': skill.get('skill_title'),
                    'rating': skill.get('rating', 1),
                    'parent_titles': skill.get('parent_titles', [])
                })
        
        return UserDetail(
            email=user['email'],
            name=user['name'],
            total_skills=len(user.get('skills', [])),
            l1_skills=skills_by_level[1],
            l2_skills=skills_by_level[2],
            l3_skills=skills_by_level[3],
            l4_skills=skills_by_level[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user detail: {str(e)}"
        )


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service status and version
    """
    try:
        # Check repository
        user_repo = get_repository()
        user_count = len(user_repo.get_all_users())
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            user_count=user_count
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            user_count=0
        )


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get application statistics.
    
    Returns:
        Stats about users, skills, and configuration
    """
    try:
        user_repo = get_repository()
        all_users = user_repo.get_all_users()
        
        # Gather stats
        total_users = len(all_users)
        total_skills = sum(len(u.get('skills', [])) for u in all_users)
        
        # Skills by level
        level_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for user in all_users:
            for skill in user.get('skills', []):
                level = skill.get('skill_level', 0)
                if level in level_counts:
                    level_counts[level] += 1
        
        # Rating distribution
        rating_counts = {1: 0, 2: 0, 3: 0}
        for user in all_users:
            for skill in user.get('skills', []):
                rating = skill.get('rating', 1)
                if rating in rating_counts:
                    rating_counts[rating] += 1
        
        return StatsResponse(
            total_users=total_users,
            total_skills=total_skills,
            skills_by_level=level_counts,
            skills_by_rating=rating_counts,
            config={
                'level_weights': {
                    'l1': settings.level_weight_l1,
                    'l2': settings.level_weight_l2,
                    'l3': settings.level_weight_l3,
                    'l4': settings.level_weight_l4
                },
                'rating_multipliers': {
                    '1': settings.rating_multiplier_1,
                    '2': settings.rating_multiplier_2,
                    '3': settings.rating_multiplier_3
                },
                'transfer_bonus': {
                    'per_tech': settings.transfer_bonus_per_tech,
                    'cap': settings.transfer_bonus_cap
                },
                'score_buckets': {
                    'excellent_min': settings.excellent_min_score,
                    'strong_min': settings.strong_min_score,
                    'good_min': settings.good_min_score
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


# Helper functions

def _build_skills_lookup(users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build a lookup table of all skills across all users.
    Maps skill_id -> skill details
    """
    skills_lookup = {}
    
    for user in users:
        for skill in user.get('skills', []):
            skill_id = skill.get('skill_id')
            if skill_id and skill_id not in skills_lookup:
                skills_lookup[skill_id] = {
                    'skill_id': skill_id,
                    'title': skill.get('skill_title', ''),
                    'level': skill.get('skill_level', 0),
                    'parent_id': skill.get('parent_id'),
                    'parent_ids': skill.get('parent_ids', []),
                    'parent_titles': skill.get('parent_titles', [])
                }
    
    return skills_lookup


def _create_score_buckets(users: List[Dict[str, Any]]) -> List[ScoreBucket]:
    """
    Organize users into score buckets.
    
    Buckets:
    - Excellent: 80-100
    - Strong: 60-79
    - Good: 40-59
    - Other: <40
    """
    buckets_config = [
        {
            'name': 'Excellent Match',
            'min_score': settings.excellent_min_score,
            'max_score': 100.0
        },
        {
            'name': 'Strong Match',
            'min_score': settings.strong_min_score,
            'max_score': settings.excellent_min_score - 0.01
        },
        {
            'name': 'Good Match',
            'min_score': settings.good_min_score,
            'max_score': settings.strong_min_score - 0.01
        },
        {
            'name': 'Other Matches',
            'min_score': 0.0,
            'max_score': settings.good_min_score - 0.01
        }
    ]
    
    buckets = []
    
    for bucket_cfg in buckets_config:
        # Filter users in this bucket
        bucket_users = [
            u for u in users
            if bucket_cfg['min_score'] <= u['score'] <= bucket_cfg['max_score']
        ]
        
        # Convert to UserResult models
        bucket_user_results = [
            UserResult(
                email=u['email'],
                name=u['name'],
                rank=u['rank'],
                score=u['score'],
                matched_skills=u['matched_skills'],
                transfer_bonus=u['transfer_bonus']
            )
            for u in bucket_users
        ]
        
        buckets.append(ScoreBucket(
            name=bucket_cfg['name'],
            min_score=bucket_cfg['min_score'],
            max_score=bucket_cfg['max_score'],
            count=len(bucket_user_results),
            users=bucket_user_results
        ))
    
    return buckets
