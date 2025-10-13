# Implementation

## Skill Flattening Algorithm

### Design Rationale

The hierarchical skills structure (L1 → L2 → L3 → L4) provides organizational clarity but isn't directly searchable. Flattening converts each node into a searchable unit while preserving hierarchy context.

### Flattening Process

Each skill at every level becomes a separate vector with:
- **id**: Unique identifier
- **level**: Hierarchy depth (1-4)
- **title**: Skill name
- **description**: Detailed explanation
- **parent_id**: Immediate parent (null for L1)
- **ancestor_ids**: Full lineage array [L1, L2, L3...] 

**Example**:
```json
{
  "id": "L4U3FUDX",
  "level": 4,
  "title": "AWS Lambda",
  "description": "Serverless compute service...",
  "parent_id": "L3227QAX",
  "ancestor_ids": ["L3227QAX", "L2B5980F", "L1VX34BJ"]
}
```

This structure enables:
- Direct search at any hierarchy level
- Parent/child relationship queries
- Ancestor chain navigation
- Context-aware embeddings

## Incremental Update Algorithm

### Change Detection

```python
def identify_changes(flat_skills, existing_embeddings):
    # Compare skill content (title + description)
    # Return only new or modified skills
```

**Benefits**:
- Saves Bedrock API costs (only embed delta)
- Faster processing on subsequent runs
- Preserves embeddings for unchanged skills

**Triggers Full Re-embedding**:
- Skill title changed
- Skill description changed
- Skill ID changed
- skill-embeddings.jsonl missing

## Prompt Engineering

### Prompt Structure

```python
def generate_prompt(skill):
    """Create rich semantic representation."""
    parts = [skill["title"]]
    
    if skill.get("description"):
        parts.append(skill["description"])
    
    # Add hierarchy context
    if skill["level"] > 1 and skill.get("ancestor_titles"):
        context = " > ".join(skill["ancestor_titles"])
        parts.append(f"Context: {context}")
    
    return " | ".join(parts)
```

**Example Prompt**:
```
AWS Lambda | Serverless compute service that runs code in response to events | Context: Cloud Computing > Compute Services > Serverless Architecture
```

**Rationale**:
- Title provides primary semantic signal
- Description adds specificity
- Hierarchy context improves semantic clustering
- Separators (`|`, `>`) help model parse structure

## Embedding Generation

### Batch Processing

```python
def generate_embeddings_batch(skills_batch):
    """Process multiple skills in one API call."""
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        body=json.dumps({
            "inputTexts": [generate_prompt(s) for s in skills_batch],
            "dimensions": EMBEDDING_DIM,
            "normalize": True
        })
    )
    return response["embeddings"]
```

**Benefits**:
- Reduces API calls (Bedrock supports batch)
- Faster processing
- Better rate limit utilization

**Trade-offs**:
- Larger batches = less granular error handling
- AWS limits: Check Bedrock batch size limits

### Normalization

Embeddings are normalized (unit length) for:
- Consistent cosine distance calculations
- Faster similarity comparisons
- Reduced storage (can use quantization)

## Vector Upload

### Batch Upload Strategy

```python
def upload_vectors_to_s3(embeddings, batch_size=50):
    """Upload in configurable batches."""
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i+batch_size]
        s3vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            vectors=[{
                "key": emb["id"],
                "float32": emb["embedding"],
                "metadata": {
                    "title": emb["title"],
                    "level": str(emb["level"]),
                    "parent_id": emb.get("parent_id", ""),
                    "ancestor_ids": json.dumps(emb["ancestor_ids"])
                }
            } for emb in batch]
        )
```

**Metadata Considerations**:
- S3 Vectors has metadata size limits
- Store full hierarchy for context
- JSON encode arrays (ancestor_ids)
- Convert numbers to strings (level)
