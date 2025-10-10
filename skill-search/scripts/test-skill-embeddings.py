#!/usr/bin/env python3
"""
Skill Embeddings Search Test
=============================
Interactive test script for querying the Skills Vector Index using natural language.

This script demonstrates semantic search capabilities by:
1. Taking a natural language query from the user (or using a default)
2. Generating an embedding for the query using AWS Bedrock Titan V2
3. Querying the S3 Vector Index to find similar skills
4. Displaying ranked results with similarity scores and interpretations

Usage:
    python3 test-skill-embeddings.py
"""

import json
import boto3
import sys
import os
from typing import List, Dict, Any, Optional

# =============================================================================
# CONFIGURATION - Must match skill-embeddings.py settings
# =============================================================================

# AWS Profiles and Regions
BEDROCK_PROFILE = "exalm"
BEDROCK_REGION = "us-east-1"
S3VECTORS_PROFILE = "troy"
S3VECTORS_REGION = "ap-southeast-2"

# Vector Bucket & Index
VECTOR_BUCKET = "skills-vectors-1760131105"  # UPDATE THIS to match your deployment
VECTOR_INDEX = "skills-index"

# Embedding Model Configuration
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIM = 1024

# Default Search Parameters
DEFAULT_TOP_K = 5
DEFAULT_QUERY = (
    "We need experienced consultants for a cloud migration project involving "
    "containerization, microservices architecture, and infrastructure automation "
    "using Kubernetes and Terraform"
)

# =============================================================================
# AWS CLIENT INITIALIZATION
# =============================================================================

print("=" * 80)
print("SKILL EMBEDDINGS SEARCH TEST")
print("=" * 80)
print()

print("Initializing AWS clients...")
print("-" * 80)

# Initialize Bedrock client for embedding generation
try:
    bedrock_session = boto3.Session(profile_name=BEDROCK_PROFILE, region_name=BEDROCK_REGION)
    bedrock = bedrock_session.client("bedrock-runtime")
    print(f"✓ Connected to Bedrock in {BEDROCK_REGION}")
except Exception as e:
    print(f"✗ Failed to initialize Bedrock client: {e}")
    sys.exit(1)

# Initialize S3 Vectors client for querying
try:
    s3vectors_session = boto3.Session(profile_name=S3VECTORS_PROFILE, region_name=S3VECTORS_REGION)
    s3vectors = s3vectors_session.client("s3vectors")
    print(f"✓ Connected to S3 Vectors in {S3VECTORS_REGION}")
except Exception as e:
    print(f"✗ Failed to initialize S3 Vectors client: {e}")
    sys.exit(1)

# Verify vector index exists
try:
    index_info = s3vectors.get_index(
        vectorBucketName=VECTOR_BUCKET,
        indexName=VECTOR_INDEX
    )
    print(f"✓ Verified vector index '{VECTOR_INDEX}' exists in bucket '{VECTOR_BUCKET}'")
    print(f"  Index dimension: {index_info.get('dimension', 'N/A')}")
    print(f"  Distance metric: {index_info.get('distanceMetric', 'N/A')}")
except Exception as e:
    print(f"✗ Vector index '{VECTOR_INDEX}' not found in bucket '{VECTOR_BUCKET}'")
    print(f"   Error: {e}")
    print(f"\n   Please run deploy-skill-search.sh and skill-embeddings.py first.")
    sys.exit(1)

print()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_query_embedding(query_text: str) -> List[float]:
    """
    Generate embedding vector for a query string using AWS Bedrock Titan V2.
    
    Args:
        query_text: Natural language query string
        
    Returns:
        List of floats representing the query embedding vector
    """
    try:
        request_body = json.dumps({
            "inputText": query_text,
            "dimensions": EMBEDDING_DIM,
            "normalize": True
        })
        
        response = bedrock.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=request_body
        )
        
        response_body = json.loads(response["body"].read())
        embedding = response_body.get("embedding")
        
        if not embedding:
            raise ValueError("No embedding returned from Bedrock")
            
        return embedding
        
    except Exception as e:
        print(f"✗ Error generating embedding: {e}")
        raise


def interpret_similarity(score: float, metric: str = "cosine") -> tuple[str, str]:
    """
    Interpret similarity score with qualitative description and color.
    
    NOTE: AWS S3 Vectors returns DISTANCE, not similarity!
    For cosine metric: distance = 1 - similarity
    Therefore: Lower distance = Better match
    
    Args:
        score: Distance score from AWS (cosine distance: 0 = identical, 1 = orthogonal)
        metric: Distance metric used (cosine or euclidean)
        
    Returns:
        Tuple of (interpretation, color_code, similarity_score)
    """
    if metric.lower() == "cosine":
        # AWS returns cosine DISTANCE (lower = better)
        # Convert to similarity for interpretation: similarity = 1 - distance
        similarity = 1 - score
        
        # Interpret based on DISTANCE thresholds (lower = better)
        # Color progression: White (Weak) → Orange → Yellow → Blue → Green (Excellent)
        if score <= 0.15:  # similarity >= 0.85
            return "Excellent Match", "🟢", similarity
        elif score <= 0.30:  # similarity >= 0.70
            return "Strong Match", "�", similarity
        elif score <= 0.45:  # similarity >= 0.55
            return "Good Match", "�", similarity
        elif score <= 0.60:  # similarity >= 0.40
            return "Moderate Match", "�", similarity
        else:  # score > 0.60
            return "Weak Match", "⚪", similarity
    else:
        # For other metrics, provide generic interpretation
        return "Match", "🔵", score


def parse_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse metadata from query results, handling JSON-encoded fields.
    
    Args:
        metadata: Raw metadata dictionary from query response
        
    Returns:
        Parsed metadata dictionary with JSON fields decoded
    """
    parsed = {}
    
    for key, value in metadata.items():
        if key == "ancestor_ids":
            # Parse JSON array
            try:
                parsed[key] = json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                parsed[key] = []
        elif key == "level":
            # Convert to integer
            try:
                parsed[key] = int(value)
            except (ValueError, TypeError):
                parsed[key] = value
        else:
            parsed[key] = value
            
    return parsed


def format_skill_level(level: int) -> str:
    """
    Format skill level as descriptive string.
    
    Args:
        level: Skill level (1-4)
        
    Returns:
        Formatted level string
    """
    level_names = {
        1: "L1 (Category)",
        2: "L2 (Sub-Category)",
        3: "L3 (Generic Skill)",
        4: "L4 (Technology/Tool)"
    }
    return level_names.get(level, f"L{level}")


def search_skills(query_text: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Search for skills using natural language query.
    
    Args:
        query_text: Natural language search query
        top_k: Number of top results to return
        
    Returns:
        List of search results with skill details and similarity scores
    """
    print("=" * 80)
    print("GENERATING QUERY EMBEDDING")
    print("=" * 80)
    print()
    print(f"Query: \"{query_text}\"")
    print()
    
    # Generate embedding for query
    print("Generating embedding vector...")
    query_embedding = generate_query_embedding(query_text)
    print(f"✓ Generated {len(query_embedding)}-dimensional embedding vector")
    print()
    
    # Query vector index
    print("=" * 80)
    print(f"QUERYING VECTOR INDEX (Top {top_k} Results)")
    print("=" * 80)
    print()
    
    try:
        response = s3vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            topK=top_k,
            queryVector={
                "float32": query_embedding
            },
            returnMetadata=True,
            returnDistance=True
        )
        
        results = response.get("vectors", [])
        print(f"✓ Found {len(results)} results")
        print()
        
        return results
        
    except Exception as e:
        print(f"✗ Error querying vector index: {e}")
        raise


def display_results(results: List[Dict[str, Any]], query_text: str):
    """
    Display search results with detailed formatting and interpretation.
    
    Args:
        results: List of search results from query_vectors
        query_text: Original query text for context
    """
    if not results:
        print("No results found.")
        return
    
    print("=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print()
    
    for idx, result in enumerate(results, 1):
        # Extract result fields
        skill_id = result.get("key", "N/A")
        distance = result.get("distance")
        metadata = result.get("metadata", {})
        
        # Parse metadata
        parsed_meta = parse_metadata(metadata)
        level = parsed_meta.get("level", "N/A")
        title = parsed_meta.get("title", "N/A")
        parent_id = parsed_meta.get("parent_id", "")
        ancestor_ids = parsed_meta.get("ancestor_ids", [])
        
        # Interpret similarity (returns interpretation, emoji, similarity_score)
        if distance is not None:
            interpretation, emoji, similarity = interpret_similarity(distance)
        else:
            interpretation, emoji, similarity = "N/A", "⚪", None
        
        # Display result
        print(f"Result #{idx}")
        print("-" * 80)
        print(f"  Skill ID:      {skill_id}")
        print(f"  Title:         {title}")
        print(f"  Level:         {format_skill_level(level)}")
        
        if distance is not None:
            print(f"  Distance:      {distance:.4f} (lower = better match)")
            print(f"  Similarity:    {similarity:.4f} {emoji} ({interpretation})")
        else:
            print(f"  Distance:      N/A")
            print(f"  Similarity:    N/A")
        
        if parent_id:
            print(f"  Parent ID:     {parent_id}")
        
        if ancestor_ids:
            print(f"  Ancestors:     {', '.join(ancestor_ids)}")
        
        print()
    
    # Provide interpretation
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()
    
    if results:
        top_result = results[0]
        top_meta = parse_metadata(top_result.get("metadata", {}))
        top_title = top_meta.get("title", "N/A")
        top_distance = top_result.get("distance")
        top_level = top_meta.get("level", "N/A")
        
        print(f"Query: \"{query_text}\"")
        print()
        
        if top_distance is not None:
            # Get interpretation
            interpretation, _, top_similarity = interpret_similarity(top_distance)
            
            print(f"The top result is '{top_title}' ({format_skill_level(top_level)}):")
            print(f"  • Distance: {top_distance:.4f} (AWS metric - lower is better)")
            print(f"  • Similarity: {top_similarity:.4f} (converted - higher is better)")
            print(f"  • Match Quality: {interpretation}")
            print()
            
            # Provide guidance based on DISTANCE (lower = better)
            if top_distance <= 0.30:
                print("✓ This is a strong to excellent semantic match! The query terms closely")
                print("  align with the skill's description and hierarchical context.")
            elif top_distance <= 0.50:
                print("✓ This is a good match. The skill is relevant to the query, though there")
                print("  may be some semantic distance between specific terms used.")
            else:
                print("⚠ The match is moderate or weak. This skill may be tangentially related,")
                print("  or the query may need refinement for better results.")
        else:
            print(f"The top result is '{top_title}' ({format_skill_level(top_level)}) but")
            print("no distance metric was returned.")
        
        print()
        print("NOTE: AWS S3 Vectors returns cosine DISTANCE (not similarity):")
        print("  • Distance = 1 - Similarity")
        print("  • Lower distance = Better match")
        print("  • Distance 0.0 = Identical vectors")
        print("  • Distance 1.0 = Orthogonal (unrelated)")
        print()
        print("The ranking demonstrates how semantic search captures conceptual similarity")
        print("beyond exact keyword matching, finding skills related in meaning even when")
        print("using different terminology.")
    
    print()


def get_user_input() -> Optional[tuple[str, int]]:
    """
    Get search query and parameters from user.
    
    Returns:
        Tuple of (query_text, top_k) or None if user wants to quit
    """
    print("=" * 80)
    print("SEARCH OPTIONS")
    print("=" * 80)
    print()
    print("1. Use default query")
    print("2. Enter custom query")
    print("3. Exit")
    print()
    
    choice = input("Select option (1-3): ").strip()
    print()
    
    if choice == "3":
        return None
    
    # Get query text
    if choice == "2":
        print("Enter your search query:")
        print("(Example: 'cloud migration and kubernetes orchestration')")
        print()
        query_text = input("Query: ").strip()
        
        if not query_text:
            print("⚠ Empty query provided. Using default query.")
            query_text = DEFAULT_QUERY
    else:
        query_text = DEFAULT_QUERY
        print(f"Using default query:")
        print(f"\"{query_text}\"")
    
    print()
    
    # Get top-k
    top_k_input = input(f"Number of results to return (default {DEFAULT_TOP_K}): ").strip()
    
    if top_k_input:
        try:
            top_k = int(top_k_input)
            if top_k < 1:
                print(f"⚠ Invalid number. Using default: {DEFAULT_TOP_K}")
                top_k = DEFAULT_TOP_K
            elif top_k > 100:
                print(f"⚠ Maximum 100 results allowed. Using 100.")
                top_k = 100
        except ValueError:
            print(f"⚠ Invalid input. Using default: {DEFAULT_TOP_K}")
            top_k = DEFAULT_TOP_K
    else:
        top_k = DEFAULT_TOP_K
    
    print()
    
    return query_text, top_k


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution loop."""
    
    print("=" * 80)
    print("INTERACTIVE SKILL SEARCH")
    print("=" * 80)
    print()
    print("This tool allows you to search for skills using natural language queries.")
    print("The semantic search finds skills based on conceptual similarity, not just")
    print("keyword matching.")
    print()
    
    while True:
        # Get user input
        user_input = get_user_input()
        
        if user_input is None:
            print("=" * 80)
            print("Exiting. Thank you for testing the skill search!")
            print("=" * 80)
            break
        
        query_text, top_k = user_input
        
        try:
            # Perform search
            results = search_skills(query_text, top_k)
            
            # Display results
            display_results(results, query_text)
            
        except Exception as e:
            print(f"✗ Search failed: {e}")
            print()
        
        # Ask if user wants to search again
        print("=" * 80)
        continue_search = input("Would you like to search again? (yes/no): ").strip().lower()
        print()
        
        if continue_search not in ["yes", "y"]:
            print("=" * 80)
            print("Exiting. Thank you for testing the skill search!")
            print("=" * 80)
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Search interrupted by user.")
        print("=" * 80)
        sys.exit(0)
