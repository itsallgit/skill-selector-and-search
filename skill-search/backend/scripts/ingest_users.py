#!/usr/bin/env python3
"""
User Data Ingestion Script

Reads user skill data from S3 bucket and creates a consolidated user_db.json file
for the Skills Search application.

Process:
1. Connect to S3 using AWS CLI profile
2. Find latest skills-selector-* bucket
3. Read all users/*.json files
4. Consolidate into single user_db.json
5. Save to backend/data/

Usage:
    python scripts/ingest_users.py [--profile PROFILE] [--bucket BUCKET] [--output PATH]
    
Note: By default uses INGESTION_AWS_PROFILE from config, falls back to AWS_PROFILE.
      You can override with --profile argument.
"""

import boto3
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_s3_client(profile: str, region: str):
    """Get S3 client with profile."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        return session.client('s3')
    except Exception as e:
        logger.error(f"Failed to create S3 client: {str(e)}")
        raise


def find_latest_bucket(s3_client, prefix: str = "skills-selector-") -> str:
    """Find the latest skills-selector-* bucket."""
    try:
        response = s3_client.list_buckets()
        buckets = [
            b['Name'] for b in response.get('Buckets', [])
            if b['Name'].startswith(prefix)
        ]
        
        if not buckets:
            raise ValueError(f"No buckets found with prefix '{prefix}'")
        
        # Sort by name (timestamp suffix ensures latest is last)
        buckets.sort()
        latest = buckets[-1]
        
        logger.info(f"Found {len(buckets)} matching bucket(s), using latest: {latest}")
        return latest
        
    except Exception as e:
        logger.error(f"Failed to find bucket: {str(e)}")
        raise


def list_user_files(s3_client, bucket: str, prefix: str = "users/") -> List[str]:
    """List all user JSON files in bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            logger.warning(f"No files found in s3://{bucket}/{prefix}")
            return []
        
        files = [
            obj['Key'] for obj in response['Contents']
            if obj['Key'].endswith('.json')
        ]
        
        logger.info(f"Found {len(files)} user files in s3://{bucket}/{prefix}")
        return files
        
    except Exception as e:
        logger.error(f"Failed to list user files: {str(e)}")
        raise


def download_user_data(s3_client, bucket: str, key: str) -> Dict[str, Any]:
    """Download and parse user JSON file."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to download {key}: {str(e)}")
        raise


def build_skills_lookup(users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build skills lookup table from users' selectedSkills."""
    skills_lookup = {}
    
    for user in users:
        for skill in user.get('selectedSkills', []):
            # Store L3 skills
            l3_id = skill.get('l3Id')
            if l3_id and l3_id not in skills_lookup:
                skills_lookup[l3_id] = {
                    'id': l3_id,
                    'l1Id': skill.get('l1Id'),
                    'l2Id': skill.get('l2Id'),
                    'type': 'l3'
                }
            
            # Store L4 skills
            for l4_id in skill.get('l4Ids', []):
                if l4_id and l4_id not in skills_lookup:
                    skills_lookup[l4_id] = {
                        'id': l4_id,
                        'l1Id': skill.get('l1Id'),
                        'l2Id': skill.get('l2Id'),
                        'l3Id': l3_id,
                        'type': 'l4'
                    }
    
    return skills_lookup


def build_indexes(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build indexes for fast lookups."""
    by_email = {}
    by_l3_skill = {}
    by_l4_skill = {}
    
    for idx, user in enumerate(users):
        email = user.get('userEmail')
        if email:
            by_email[email] = idx
        
        for skill in user.get('selectedSkills', []):
            l3_id = skill.get('l3Id')
            if l3_id:
                if l3_id not in by_l3_skill:
                    by_l3_skill[l3_id] = []
                by_l3_skill[l3_id].append(idx)
            
            for l4_id in skill.get('l4Ids', []):
                if l4_id:
                    if l4_id not in by_l4_skill:
                        by_l4_skill[l4_id] = []
                    by_l4_skill[l4_id].append(idx)
    
    return {
        'by_email': by_email,
        'by_l3_skill': by_l3_skill,
        'by_l4_skill': by_l4_skill
    }


def ingest_users(
    profile: str = None,
    region: str = None,
    bucket: str = None,
    output_path: str = None
) -> int:
    """
    Main ingestion process.
    
    Args:
        profile: AWS profile (defaults to ingestion_aws_profile from config)
        region: AWS region (defaults to ingestion_aws_region from config)
        bucket: S3 bucket name (auto-detects if not provided)
        output_path: Output file path
    
    Returns:
        Number of users ingested
    """
    # Use config defaults if not provided
    if profile is None:
        profile = settings.get_ingestion_profile()
    if region is None:
        region = settings.get_ingestion_region()
    
    # Default output path
    if output_path is None:
        output_path = Path(__file__).parent.parent / "data" / "user_db.json"
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting user data ingestion...")
    logger.info(f"AWS Profile: {profile}")
    logger.info(f"AWS Region: {region}")
    
    # Get S3 client
    s3_client = get_s3_client(profile, region)
    
    # Get bucket name (use provided or config default)
    if bucket is None:
        bucket = settings.ingestion_bucket
        logger.info(f"Using bucket from config: {bucket}")
    else:
        logger.info(f"Using specified bucket: {bucket}")
    
    # List user files
    user_files = list_user_files(s3_client, bucket)
    
    if not user_files:
        logger.error("No user files found")
        return 0
    
    # Download and consolidate
    users = []
    for i, key in enumerate(user_files, 1):
        logger.info(f"[{i}/{len(user_files)}] Downloading {key}...")
        try:
            user_data = download_user_data(s3_client, bucket, key)
            users.append(user_data)
        except Exception as e:
            logger.warning(f"Skipping {key} due to error: {str(e)}")
            continue
    
    if not users:
        logger.error("No valid user data downloaded")
        return 0
    
    # Build skills lookup and indexes
    logger.info("Building skills lookup table...")
    skills_lookup = build_skills_lookup(users)
    
    logger.info("Building indexes...")
    indexes = build_indexes(users)
    
    # Build final structure
    from datetime import datetime
    db_structure = {
        "metadata": {
            "ingested_at": datetime.utcnow().isoformat() + "Z",
            "source_bucket": bucket,
            "user_count": len(users),
            "skill_count": len(skills_lookup)
        },
        "skills_lookup": skills_lookup,
        "users": users,
        "indexes": indexes
    }
    
    # Save consolidated file
    logger.info(f"Writing {len(users)} users to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db_structure, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Ingestion complete! {len(users)} users saved to {output_path}")
    
    # Print summary
    total_skills = sum(len(u.get('selectedSkills', [])) for u in users)
    logger.info(f"Summary: {len(users)} users, {total_skills} total skill selections, {len(skills_lookup)} unique skills")
    
    return len(users)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest user skill data from S3 into local database",
        epilog=f"Default profile from config: {settings.get_ingestion_profile()}"
    )
    parser.add_argument(
        '--profile',
        default=None,
        help=f'AWS CLI profile name (default: {settings.get_ingestion_profile()} from config)'
    )
    parser.add_argument(
        '--region',
        default=None,
        help=f'AWS region (default: {settings.get_ingestion_region()} from config)'
    )
    parser.add_argument(
        '--bucket',
        required=False,
        help=f'S3 bucket name (default: {settings.ingestion_bucket} from config)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: backend/data/user_db.json)'
    )
    
    args = parser.parse_args()
    
    try:
        count = ingest_users(
            profile=args.profile,
            region=args.region,
            bucket=args.bucket,
            output_path=args.output
        )
        
        if count > 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
