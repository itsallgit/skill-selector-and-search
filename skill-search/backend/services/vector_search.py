"""
Vector Search Service - Handles embedding generation and vector index queries.
"""

import json
import boto3
from typing import List, Dict, Any, Tuple
from config import settings


class VectorSearchService:
    """Service for generating embeddings and querying vector index."""
    
    def __init__(self):
        """Initialize AWS clients for Bedrock and S3 Vectors."""
        # Bedrock client for embedding generation
        # Uses task-specific profile or falls back to default
        bedrock_session = boto3.Session(
            profile_name=settings.get_embedding_profile(),
            region_name=settings.get_embedding_region()
        )
        self.bedrock = bedrock_session.client("bedrock-runtime")
        
        # S3 Vectors client for querying
        # Uses task-specific profile or falls back to default
        s3vectors_session = boto3.Session(
            profile_name=settings.get_vector_profile(),
            region_name=settings.get_vector_region()
        )
        self.s3vectors = s3vectors_session.client("s3vectors")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using AWS Bedrock Titan V2.
        
        Args:
            text: Natural language text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        request_body = json.dumps({
            "inputText": text,
            "dimensions": settings.embedding_dim,
            "normalize": True
        })
        
        response = self.bedrock.invoke_model(
            modelId=settings.embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=request_body
        )
        
        response_body = json.loads(response["body"].read())
        embedding = response_body.get("embedding")
        
        if not embedding:
            raise ValueError("No embedding returned from Bedrock")
        
        return embedding
    
    def query_vector_index(
        self,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Query the S3 Vector Index for similar skills.
        
        Args:
            query_embedding: Query vector (1024 dimensions)
            top_k: Number of results to return
            
        Returns:
            List of matched skills with metadata and distances
        """
        if top_k is None:
            top_k = settings.top_k_skills
        
        # Query vector index
        response = self.s3vectors.query_vectors(
            vectorBucketName=settings.vector_bucket,
            indexName=settings.vector_index,
            topK=top_k,
            queryVector={
                "float32": query_embedding
            },
            returnMetadata=True,
            returnDistance=True
        )
        
        return response.get("vectors", [])
    
    def interpret_distance(self, distance: float) -> Tuple[str, str, float]:
        """
        Interpret cosine distance as similarity with qualitative description.
        
        AWS S3 Vectors returns cosine DISTANCE (lower = better):
        - distance = 1 - similarity
        - similarity = 1 - distance
        
        Args:
            distance: Cosine distance from vector search
            
        Returns:
            Tuple of (interpretation, emoji, similarity)
        """
        similarity = 1 - distance
        
        # Color progression: White (Weak) → Orange → Yellow → Blue → Green (Excellent)
        if distance <= 0.15:  # similarity >= 0.85
            return "Excellent Match", "🟢", similarity
        elif distance <= 0.30:  # similarity >= 0.70
            return "Strong Match", "🔵", similarity
        elif distance <= 0.45:  # similarity >= 0.55
            return "Good Match", "🟡", similarity
        elif distance <= 0.60:  # similarity >= 0.40
            return "Moderate Match", "🟠", similarity
        else:  # distance > 0.60
            return "Weak Match", "⚪", similarity
    
    def search_skills(self, query_text: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        High-level method to search for skills using natural language.
        
        Args:
            query_text: Natural language query
            top_k: Number of results to return
            
        Returns:
            List of matched skills with interpreted results
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_text)
        
        # Query vector index
        raw_results = self.query_vector_index(query_embedding, top_k)
        
        # Process and interpret results
        processed_results = []
        for result in raw_results:
            skill_id = result.get("key")
            distance = result.get("distance")
            metadata = result.get("metadata", {})
            
            interpretation, emoji, similarity = self.interpret_distance(distance)
            
            # Parse metadata
            level = int(metadata.get("level", 0))
            title = metadata.get("title", "Unknown")
            parent_id = metadata.get("parent_id", "")
            
            # Try to parse ancestor_ids if it's a JSON string
            ancestor_ids = metadata.get("ancestor_ids", "[]")
            if isinstance(ancestor_ids, str):
                try:
                    ancestor_ids = json.loads(ancestor_ids)
                except json.JSONDecodeError:
                    ancestor_ids = []
            
            processed_results.append({
                "skill_id": skill_id,
                "title": title,
                "level": level,
                "distance": distance,
                "similarity": similarity,
                "interpretation": interpretation,
                "emoji": emoji,
                "parent_id": parent_id,
                "ancestor_ids": ancestor_ids,
                "metadata": metadata
            })
        
        return processed_results


# Singleton instance
_vector_search_service: VectorSearchService = None


def get_vector_search_service() -> VectorSearchService:
    """Get the global vector search service instance."""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
