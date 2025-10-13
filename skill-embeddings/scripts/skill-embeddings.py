#!/usr/bin/env python3
"""
Skill Embeddings Generator
===========================
Generates semantic embeddings for skills from skills-master.json and uploads
them to an AWS S3 Vector Index for semantic search capabilities.

This script:
1. Flattens the hierarchical skills-master.json structure
2. Compares with existing skill-embeddings.jsonl to detect changes
3. Generates embeddings for new/changed skills using AWS Bedrock Titan V2
4. Saves all embeddings to skill-embeddings.jsonl
5. Batch uploads all vectors to the S3 Vector Index

Usage:
    python3 skill-embeddings.py

Configuration:
    Dynamic configuration values (AWS profiles, regions, bucket) are loaded from
    skill-embeddings-config.json. Run skill-embeddings-setup.sh first to generate
    this configuration file.
"""

import json
import boto3
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# =============================================================================
# LOAD DYNAMIC CONFIGURATION
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "../skill-embeddings-config.json")

# Check if config file exists
if not os.path.exists(CONFIG_FILE):
    print("=" * 80)
    print("ERROR: Configuration file not found")
    print("=" * 80)
    print(f"\nThe configuration file does not exist: {CONFIG_FILE}")
    print("\nPlease run the setup script first:")
    print("  ./skill-embeddings/skill-embeddings-setup.sh")
    print("\nOr from the project menu:")
    print("  Main Menu → Skill Embeddings → Setup & Run Embeddings")
    print()
    sys.exit(1)

# Load configuration
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    # Dynamic configuration (set by setup script)
    BEDROCK_PROFILE = config["bedrock_profile"]
    BEDROCK_REGION = config["bedrock_region"]
    S3VECTORS_PROFILE = config["s3vectors_profile"]
    S3VECTORS_REGION = config["s3vectors_region"]
    VECTOR_BUCKET = config["vector_bucket"]
    VECTOR_INDEX = config["vector_index"]
except Exception as e:
    print("=" * 80)
    print("ERROR: Failed to load configuration")
    print("=" * 80)
    print(f"\nError reading {CONFIG_FILE}: {e}")
    print("\nPlease run the setup script to regenerate the configuration:")
    print("  ./skill-embeddings/skill-embeddings-setup.sh")
    print()
    sys.exit(1)

# =============================================================================
# STATIC CONFIGURATION
# =============================================================================

# Embedding Model Configuration (static)
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIM = 1024
DISTANCE_METRIC = "cosine"

# File Paths (relative to script location)
SKILLS_MASTER_PATH = os.path.join(SCRIPT_DIR, "../../data/skills-master.json")
EMBEDDINGS_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "../../data/skill-embeddings.jsonl")

# Processing Configuration (static)
EMBEDDING_BATCH_SIZE = 25  # Number of skills to embed per Bedrock API call
MAX_VECTORS_PER_UPLOAD = 50  # Number of vectors to upload per S3 Vectors API call

# =============================================================================
# SCRIPT INITIALIZATION
# =============================================================================

print("=" * 80)
print("SKILL EMBEDDINGS GENERATOR")
print("=" * 80)
print("\nConfiguration:")
print(f"  Bedrock Profile: {BEDROCK_PROFILE} (Region: {BEDROCK_REGION})")
print(f"  S3 Vectors Profile: {S3VECTORS_PROFILE} (Region: {S3VECTORS_REGION})")
print(f"  Vector Bucket: {VECTOR_BUCKET}")
print(f"  Vector Index: {VECTOR_INDEX}")
print(f"  Embedding Model: {EMBEDDING_MODEL_ID}")
print(f"  Embedding Dimension: {EMBEDDING_DIM}")
print(f"  Distance Metric: {DISTANCE_METRIC}")
print(f"  Skills Master: {SKILLS_MASTER_PATH}")
print(f"  Output JSONL: {EMBEDDINGS_OUTPUT_PATH}")
print(f"  Embedding Batch Size: {EMBEDDING_BATCH_SIZE}")
print(f"  Upload Batch Size: {MAX_VECTORS_PER_UPLOAD}")
print()

# Initialize AWS clients with profiles
try:
    bedrock_session = boto3.Session(profile_name=BEDROCK_PROFILE, region_name=BEDROCK_REGION)
    bedrock = bedrock_session.client("bedrock-runtime")
    print(f"✓ Connected to Bedrock in {BEDROCK_REGION}")
except Exception as e:
    print(f"✗ Failed to initialize Bedrock client: {e}")
    sys.exit(1)

try:
    s3vectors_session = boto3.Session(profile_name=S3VECTORS_PROFILE, region_name=S3VECTORS_REGION)
    s3vectors = s3vectors_session.client("s3vectors")
    print(f"✓ Connected to S3 Vectors in {S3VECTORS_REGION}")
except Exception as e:
    print(f"✗ Failed to initialize S3 Vectors client: {e}")
    sys.exit(1)

# Verify vector index exists
try:
    s3vectors.get_index(
        vectorBucketName=VECTOR_BUCKET,
        indexName=VECTOR_INDEX
    )
    print(f"✓ Verified vector index '{VECTOR_INDEX}' exists in bucket '{VECTOR_BUCKET}'")
except Exception as e:
    print(f"✗ Vector index '{VECTOR_INDEX}' not found in bucket '{VECTOR_BUCKET}'")
    print(f"   Error: {e}")
    print(f"\n   Please run deploy-skill-search.sh first to create the vector index.")
    sys.exit(1)

print()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def flatten_skills(master_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Recursively flatten the hierarchical skills-master.json into a flat list.
    
    Each flattened skill contains:
    - id, level, title, description
    - parent_id: ID of immediate parent (None for L1)
    - ancestor_ids: List of all ancestor IDs from top to immediate parent
    
    Args:
        master_list: Top-level list from skills-master.json
        
    Returns:
        List of flattened skill dictionaries
    """
    flat = []
    
    def recurse(node: Dict[str, Any], parent_id: Optional[str], ancestor_ids: List[str]):
        """Recursively process each node in the hierarchy."""
        skill = {
            "id": node["id"],
            "level": node["level"],
            "title": node.get("title", ""),
            "description": node.get("description", ""),
            "parent_id": parent_id,
            "ancestor_ids": ancestor_ids.copy()
        }
        flat.append(skill)
        
        # Recursively process children
        for child in node.get("skills", []):
            recurse(child, node["id"], ancestor_ids + [node["id"]])
    
    # Process all top-level skills
    for top in master_list:
        recurse(top, parent_id=None, ancestor_ids=[])
    
    return flat


def compose_embedding_text(skill: Dict[str, Any], skill_map: Dict[str, Dict[str, Any]]) -> str:
    """
    Compose natural language text for embedding generation.
    
    Format: "<title> - <description>. This is a <parent_title> <skill_type> 
            within the broader <grandparent_title> domain."
    
    This natural language format aligns with how embedding models are trained,
    providing better semantic representations than structured formats.
    
    Args:
        skill: Flattened skill dictionary
        skill_map: Map of skill ID to skill data for parent lookups
        
    Returns:
        Natural language embedding text
    """
    title = skill["title"]
    description = skill["description"]
    level = skill["level"]
    
    # Start with title and description
    text_parts = [f"{title} - {description}"]
    
    # Add hierarchical context if available
    if level >= 2 and skill["parent_id"]:
        parent = skill_map[skill["parent_id"]]
        parent_title = parent["title"]
        
        if level >= 3 and len(skill["ancestor_ids"]) >= 2:
            # Has grandparent (for L3 and L4)
            grandparent = skill_map[skill["ancestor_ids"][-2]]
            grandparent_title = grandparent["title"]
            
            # Determine skill type based on level
            skill_type = {
                2: "capability",
                3: "skill",
                4: "technology"
            }.get(level, "skill")
            
            text_parts.append(
                f"This is a {parent_title} {skill_type} within the broader {grandparent_title} domain."
            )
        else:
            # Only has parent (for L2)
            text_parts.append(f"This is part of {parent_title}.")
    
    return " ".join(text_parts)


def load_existing_embeddings() -> Tuple[Dict[str, Dict[str, Any]], Optional[str]]:
    """
    Load existing skill-embeddings.jsonl file if it exists.
    
    Returns:
        Tuple of (skill_map, last_updated_timestamp)
        - skill_map: Dictionary mapping skill ID to full skill data with embeddings
        - last_updated_timestamp: Timestamp from metadata, if available
    """
    if not os.path.exists(EMBEDDINGS_OUTPUT_PATH):
        print(f"ℹ No existing embeddings file found at {EMBEDDINGS_OUTPUT_PATH}")
        return {}, None
    
    skill_map = {}
    last_updated = None
    
    try:
        with open(EMBEDDINGS_OUTPUT_PATH, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Check if this is metadata line
                    if data.get("_metadata"):
                        last_updated = data["_metadata"].get("last_updated")
                        continue
                    
                    # Regular skill data
                    skill_map[data["id"]] = data
                    
                except json.JSONDecodeError as e:
                    print(f"  Warning: Skipping malformed JSON on line {line_num}: {e}")
                    continue
        
        print(f"✓ Loaded {len(skill_map)} existing embeddings")
        if last_updated:
            print(f"  Last updated: {last_updated}")
        
    except Exception as e:
        print(f"  Warning: Error reading embeddings file: {e}")
        return {}, None
    
    return skill_map, last_updated


def detect_changes(new_skills: List[Dict[str, Any]], 
                   existing_embeddings: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Compare new skills with existing embeddings to detect changes.
    
    A skill is considered changed if:
    - It's new (ID not in existing embeddings)
    - Title or description has changed
    - Parent or ancestors have changed (affects context)
    
    Args:
        new_skills: Flattened skills from current skills-master.json
        existing_embeddings: Map of existing skill embeddings
        
    Returns:
        Tuple of (changed_skills, unchanged_skill_ids)
    """
    changed = []
    unchanged_ids = []
    
    for skill in new_skills:
        skill_id = skill["id"]
        
        if skill_id not in existing_embeddings:
            # New skill
            changed.append(skill)
        else:
            # Check if content changed
            existing = existing_embeddings[skill_id]
            
            content_changed = (
                skill["title"] != existing.get("title") or
                skill["description"] != existing.get("description") or
                skill["parent_id"] != existing.get("parent_id") or
                skill["ancestor_ids"] != existing.get("ancestor_ids")
            )
            
            if content_changed:
                changed.append(skill)
            else:
                unchanged_ids.append(skill_id)
    
    return changed, unchanged_ids


def embed_texts_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using AWS Bedrock Titan V2.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each vector is a list of floats)
    """
    embeddings = []
    
    for text in texts:
        try:
            # Prepare request payload
            payload = {
                "inputText": text,
                "dimensions": EMBEDDING_DIM,
                "normalize": True  # Normalize for cosine similarity
            }
            
            # Call Bedrock
            response = bedrock.invoke_model(
                modelId=EMBEDDING_MODEL_ID,
                body=json.dumps(payload)
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body["embedding"]
            
            embeddings.append(embedding)
            
        except Exception as e:
            print(f"    Error embedding text: {e}")
            print(f"    Text preview: {text[:100]}...")
            raise
    
    return embeddings


def save_embeddings_jsonl(all_skills: List[Dict[str, Any]], 
                          skill_map: Dict[str, Dict[str, Any]],
                          existing_embeddings: Dict[str, Dict[str, Any]]):
    """
    Save all skill embeddings to JSONL file.
    
    The file contains:
    - Metadata line with last_updated timestamp
    - One line per skill with complete data
    
    Args:
        all_skills: All flattened skills (current state)
        skill_map: Map for looking up parents
        existing_embeddings: Existing embeddings to preserve for unchanged skills
    """
    print("\n" + "=" * 80)
    print("STAGE 4: SAVING EMBEDDINGS TO JSONL")
    print("=" * 80)
    
    with open(EMBEDDINGS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        # Write metadata line
        metadata = {
            "_metadata": {
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "total_skills": len(all_skills),
                "embedding_model": EMBEDDING_MODEL_ID,
                "embedding_dim": EMBEDDING_DIM
            }
        }
        f.write(json.dumps(metadata) + "\n")
        
        # Write all skills
        for skill in all_skills:
            skill_id = skill["id"]
            
            # Use existing embedding if available and unchanged
            if skill_id in existing_embeddings and "vector" in existing_embeddings[skill_id]:
                existing = existing_embeddings[skill_id]
                output = {
                    "id": skill_id,
                    "level": skill["level"],
                    "title": skill["title"],
                    "description": skill["description"],
                    "parent_id": skill["parent_id"],
                    "ancestor_ids": skill["ancestor_ids"],
                    "embedding_text": existing.get("embedding_text", ""),
                    "vector": existing["vector"]
                }
            else:
                # This shouldn't happen if we processed correctly, but handle gracefully
                print(f"  Warning: Missing embedding for {skill_id}, skipping...")
                continue
            
            f.write(json.dumps(output) + "\n")
    
    print(f"✓ Saved {len(all_skills)} skill embeddings to {EMBEDDINGS_OUTPUT_PATH}")


def upload_vectors_batch(skills_data: List[Dict[str, Any]]):
    """
    Upload a batch of skill vectors to S3 Vector Index.
    
    Args:
        skills_data: List of skill dictionaries with 'id' and 'vector' fields
    
    Note:
        The 'data' field must be a tagged union with 'float32' key as per AWS API requirements.
        Metadata values must be JSON-serializable strings.
    """
    if not skills_data:
        return
    
    # Prepare vectors for upload with correct AWS S3 Vectors API structure
    vectors = []
    for skill in skills_data:
        # Ensure vector data is float32 (AWS requirement)
        vector_data = [float(v) for v in skill["vector"]]
        
        # Prepare metadata - convert lists to JSON strings for API compatibility
        metadata = {
            "level": str(skill["level"]),
            "title": skill["title"],
            "parent_id": skill.get("parent_id") or "",
            "ancestor_ids": json.dumps(skill.get("ancestor_ids", []))  # Convert list to JSON string
        }
        
        vectors.append({
            "key": skill["id"],
            "data": {
                "float32": vector_data  # Tagged union structure required by AWS API
            },
            "metadata": metadata
        })
    
    try:
        response = s3vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            vectors=vectors
        )
        return response
    except Exception as e:
        print(f"    Error uploading batch: {e}")
        raise


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution flow."""
    
    # Stage 1: Load and flatten skills
    print("=" * 80)
    print("STAGE 1: LOADING AND FLATTENING SKILLS")
    print("=" * 80)
    
    if not os.path.exists(SKILLS_MASTER_PATH):
        print(f"✗ Skills master file not found: {SKILLS_MASTER_PATH}")
        print(f"   Please ensure the file exists at the configured path.")
        sys.exit(1)
    
    try:
        with open(SKILLS_MASTER_PATH, 'r', encoding='utf-8') as f:
            master_skills = json.load(f)
        print(f"✓ Loaded skills-master.json")
    except Exception as e:
        print(f"✗ Failed to load skills-master.json: {e}")
        sys.exit(1)
    
    flattened_skills = flatten_skills(master_skills)
    skill_map = {s["id"]: s for s in flattened_skills}
    
    print(f"✓ Flattened {len(flattened_skills)} skills from hierarchy")
    
    # Stage 2: Load existing embeddings and detect changes
    print("\n" + "=" * 80)
    print("STAGE 2: DETECTING CHANGES")
    print("=" * 80)
    
    existing_embeddings, last_updated = load_existing_embeddings()
    changed_skills, unchanged_ids = detect_changes(flattened_skills, existing_embeddings)
    
    print(f"\nChange Summary:")
    print(f"  Total skills: {len(flattened_skills)}")
    print(f"  Unchanged: {len(unchanged_ids)}")
    print(f"  New or modified: {len(changed_skills)}")
    
    if changed_skills:
        print(f"\n  Changed skills:")
        for skill in changed_skills[:10]:  # Show first 10
            status = "NEW" if skill["id"] not in existing_embeddings else "MODIFIED"
            print(f"    [{status}] {skill['id']}: {skill['title']}")
        if len(changed_skills) > 10:
            print(f"    ... and {len(changed_skills) - 10} more")
    
    # Stage 3: Generate embeddings for changed skills
    if changed_skills:
        print("\n" + "=" * 80)
        print("STAGE 3: GENERATING EMBEDDINGS")
        print("=" * 80)
        print(f"Processing {len(changed_skills)} skills in batches of {EMBEDDING_BATCH_SIZE}...")
        
        # Compose embedding texts
        embedding_texts = []
        for skill in changed_skills:
            text = compose_embedding_text(skill, skill_map)
            embedding_texts.append(text)
        
        # Generate embeddings in batches
        all_embeddings = []
        total_batches = (len(embedding_texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        
        for i in range(0, len(embedding_texts), EMBEDDING_BATCH_SIZE):
            batch_num = i // EMBEDDING_BATCH_SIZE + 1
            batch_texts = embedding_texts[i:i + EMBEDDING_BATCH_SIZE]
            
            print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch_texts)} skills)...")
            
            batch_embeddings = embed_texts_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)
        
        print(f"✓ Generated {len(all_embeddings)} embeddings")
        
        # Update skill data with new embeddings
        for skill, text, embedding in zip(changed_skills, embedding_texts, all_embeddings):
            existing_embeddings[skill["id"]] = {
                "id": skill["id"],
                "level": skill["level"],
                "title": skill["title"],
                "description": skill["description"],
                "parent_id": skill["parent_id"],
                "ancestor_ids": skill["ancestor_ids"],
                "embedding_text": text,
                "vector": embedding
            }
    else:
        print("\n✓ No changes detected - all skills are up to date")
    
    # Stage 4: Save all embeddings to JSONL
    save_embeddings_jsonl(flattened_skills, skill_map, existing_embeddings)
    
    # Stage 5: Upload to vector index
    print("\n" + "=" * 80)
    print("STAGE 5: UPLOADING TO VECTOR INDEX")
    print("=" * 80)
    print(f"Uploading {len(flattened_skills)} vectors in batches of {MAX_VECTORS_PER_UPLOAD}...")
    
    # Prepare all skills for upload (from existing_embeddings which now includes new ones)
    upload_data = []
    for skill in flattened_skills:
        if skill["id"] in existing_embeddings:
            upload_data.append(existing_embeddings[skill["id"]])
    
    # Upload in batches
    total_batches = (len(upload_data) + MAX_VECTORS_PER_UPLOAD - 1) // MAX_VECTORS_PER_UPLOAD
    uploaded_count = 0
    
    for i in range(0, len(upload_data), MAX_VECTORS_PER_UPLOAD):
        batch_num = i // MAX_VECTORS_PER_UPLOAD + 1
        batch_data = upload_data[i:i + MAX_VECTORS_PER_UPLOAD]
        
        print(f"  Uploading batch {batch_num}/{total_batches} ({len(batch_data)} vectors)...")
        
        try:
            upload_vectors_batch(batch_data)
            uploaded_count += len(batch_data)
        except Exception as e:
            print(f"✗ Failed to upload batch {batch_num}: {e}")
            print(f"   Uploaded {uploaded_count} vectors before failure")
            sys.exit(1)
    
    print(f"✓ Uploaded {uploaded_count} vectors to index '{VECTOR_INDEX}'")
    
    # Final summary
    print("\n" + "=" * 80)
    print("COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"✓ Total skills processed: {len(flattened_skills)}")
    print(f"✓ New embeddings generated: {len(changed_skills)}")
    print(f"✓ Vectors uploaded to S3: {uploaded_count}")
    print(f"✓ JSONL file saved: {EMBEDDINGS_OUTPUT_PATH}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
