#!/usr/bin/env python3
"""
AWS Validation Script

Validates AWS credentials and required services for Skills Search application.

Checks:
- AWS CLI profile exists and is valid
- Access to Bedrock (for embeddings)
- Access to S3 Vectors (for vector search)
- Required S3 buckets exist

Usage:
    python scripts/validate_aws.py [--profile PROFILE]
"""

import boto3
import sys
import argparse
from typing import Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_credentials(profile: str, region: str) -> Tuple[bool, str]:
    """Validate AWS credentials."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        logger.info(f"✓ AWS credentials valid")
        logger.info(f"  Account: {identity['Account']}")
        logger.info(f"  User: {identity['Arn']}")
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"✗ AWS credentials invalid: {str(e)}")
        return False, str(e)


def validate_bedrock(profile: str, region: str, model_id: str) -> Tuple[bool, str]:
    """Validate access to Bedrock."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        bedrock = session.client('bedrock-runtime')
        
        # Test embedding generation with small payload
        test_payload = {
            "inputText": "test",
            "dimensions": 1024,
            "normalize": True
        }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=str(test_payload).encode('utf-8')
        )
        
        logger.info(f"✓ Bedrock access valid")
        logger.info(f"  Model: {model_id}")
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"✗ Bedrock access failed: {str(e)}")
        return False, str(e)


def validate_s3vectors(profile: str, region: str, index_name: str) -> Tuple[bool, str]:
    """Validate access to S3 Vectors."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        s3vectors = session.client('s3vectors')
        
        # Test vector search with small query
        test_vector = [0.0] * 1024  # Empty vector
        
        response = s3vectors.query_vector_index(
            vectorIndexName=index_name,
            queryVector=test_vector,
            topK=1
        )
        
        logger.info(f"✓ S3 Vectors access valid")
        logger.info(f"  Index: {index_name}")
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"✗ S3 Vectors access failed: {str(e)}")
        return False, str(e)


def validate_s3_bucket(profile: str, region: str, bucket_prefix: str) -> Tuple[bool, str]:
    """Validate S3 bucket exists."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        s3 = session.client('s3')
        
        # List buckets with prefix
        response = s3.list_buckets()
        buckets = [
            b['Name'] for b in response.get('Buckets', [])
            if b['Name'].startswith(bucket_prefix)
        ]
        
        if not buckets:
            logger.warning(f"⚠ No buckets found with prefix '{bucket_prefix}'")
            return False, f"No buckets found with prefix '{bucket_prefix}'"
        
        latest = sorted(buckets)[-1]
        logger.info(f"✓ S3 bucket found: {latest}")
        return True, latest
        
    except Exception as e:
        logger.error(f"✗ S3 bucket validation failed: {str(e)}")
        return False, str(e)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate AWS credentials and services for Skills Search"
    )
    parser.add_argument(
        '--profile',
        default='default',
        help='AWS CLI profile name (default: default)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--model-id',
        default='amazon.titan-embed-text-v2:0',
        help='Bedrock model ID (default: amazon.titan-embed-text-v2:0)'
    )
    parser.add_argument(
        '--index-name',
        default='skills-index',
        help='S3 Vectors index name (default: skills-index)'
    )
    parser.add_argument(
        '--bucket-prefix',
        default='skills-selector-',
        help='S3 bucket prefix (default: skills-selector-)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("AWS VALIDATION")
    logger.info("=" * 60)
    logger.info(f"Profile: {args.profile}")
    logger.info(f"Region: {args.region}")
    logger.info("")
    
    checks = []
    
    # 1. Credentials
    logger.info("1. Checking AWS credentials...")
    valid, msg = validate_credentials(args.profile, args.region)
    checks.append(valid)
    logger.info("")
    
    # 2. Bedrock
    logger.info("2. Checking Bedrock access...")
    valid, msg = validate_bedrock(args.profile, args.region, args.model_id)
    checks.append(valid)
    logger.info("")
    
    # 3. S3 Vectors
    logger.info("3. Checking S3 Vectors access...")
    valid, msg = validate_s3vectors(args.profile, args.region, args.index_name)
    checks.append(valid)
    logger.info("")
    
    # 4. S3 Bucket
    logger.info("4. Checking S3 bucket...")
    valid, msg = validate_s3_bucket(args.profile, args.region, args.bucket_prefix)
    checks.append(valid)
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if all(checks):
        logger.info(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        logger.info("")
        logger.info("You're ready to run the Skills Search application!")
        sys.exit(0)
    else:
        logger.error(f"✗ SOME CHECKS FAILED ({passed}/{total})")
        logger.info("")
        logger.info("Please fix the issues above before running the application.")
        sys.exit(1)


if __name__ == "__main__":
    main()
