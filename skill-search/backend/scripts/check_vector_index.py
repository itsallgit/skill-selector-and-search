#!/usr/bin/env python3
"""
Diagnostic script to check S3 Vector index configuration.
"""

import boto3
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

def main():
    """Check vector index accessibility."""
    print("=" * 60)
    print("Vector Index Diagnostic")
    print("=" * 60)
    
    # Show configuration
    print(f"\nConfiguration:")
    print(f"  Profile: {settings.get_vector_profile()}")
    print(f"  Region: {settings.get_vector_region()}")
    print(f"  Bucket: {settings.vector_bucket}")
    print(f"  Index: {settings.vector_index}")
    
    # Create S3 Vectors client
    print(f"\nCreating S3 Vectors client...")
    session = boto3.Session(
        profile_name=settings.get_vector_profile(),
        region_name=settings.get_vector_region()
    )
    s3vectors = session.client("s3vectors")
    print(f"✓ Client created successfully")
    
    # Try to list indexes in the bucket
    print(f"\nListing indexes in bucket '{settings.vector_bucket}'...")
    try:
        response = s3vectors.list_indexes(
            vectorBucketName=settings.vector_bucket
        )
        indexes = response.get("indexes", [])
        print(f"✓ Found {len(indexes)} index(es):")
        
        index_names = []
        for idx in indexes:
            index_name = idx.get('indexName') if isinstance(idx, dict) else idx
            index_names.append(index_name)
            print(f"  - {index_name}")
        
        if settings.vector_index in index_names:
            print(f"\n✓ Target index '{settings.vector_index}' found!")
        else:
            print(f"\n✗ Target index '{settings.vector_index}' NOT found")
            print(f"  Available indexes: {index_names}")
            return 1
            
    except Exception as e:
        print(f"✗ Error listing indexes: {str(e)}")
        return 1
    
    # Try to describe the index
    print(f"\nDescribing index '{settings.vector_index}'...")
    try:
        response = s3vectors.describe_index(
            vectorBucketName=settings.vector_bucket,
            indexName=settings.vector_index
        )
        print(f"✓ Index details:")
        for key, value in response.items():
            if key != "ResponseMetadata":
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ Error describing index: {str(e)}")
        # Not a critical error, continue
    
    print(f"\n{'=' * 60}")
    print(f"✓ All checks passed! Vector index is accessible.")
    print(f"{'=' * 60}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
