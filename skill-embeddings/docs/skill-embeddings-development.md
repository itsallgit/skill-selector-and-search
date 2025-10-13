# Development

## Project Structure

```
skill-embeddings/
├── scripts/
│   ├── skill-embeddings.py       # Main generator script
│   └── test-skill-embeddings.py  # Interactive search test
├── infra/
│   └── deploy-skill-embeddings.sh # Infrastructure deployment
├── requirements.txt               # Python dependencies
└── docs/                          # This documentation
```

## Script Architecture

### skill-embeddings.py

Main script with these functions:

- `flatten_skills()` - Converts hierarchy to flat list with metadata
- `load_existing_embeddings()` - Reads skill-embeddings.jsonl
- `identify_changes()` - Detects delta for incremental updates
- `generate_prompt()` - Creates embedding prompt from skill data
- `generate_embeddings_batch()` - Calls Bedrock for multiple skills
- `save_embeddings()` - Writes to JSONL format
- `upload_vectors_to_s3()` - Batch uploads to S3 Vectors

### test-skill-embeddings.py

Interactive test tool:
- Accepts natural language queries
- Generates query embeddings
- Searches vector index
- Displays ranked results with similarity scores
- Interprets match quality

## Extending the Generator

### Custom Prompt Engineering

Modify `generate_prompt()` to change how skills are represented:

```python
def generate_prompt(skill: Dict[str, Any]) -> str:
    """Customize this to change embedding semantics."""
    # Current: Uses title + description + hierarchy
    # You can add: examples, synonyms, related terms, etc.
```

### Metadata Enhancement

Add fields to flattened skills in `flatten_skills()`:

```python
skill = {
    "id": node["id"],
    "level": node["level"],
    "title": node.get("title", ""),
    "description": node.get("description", ""),
    "parent_id": parent_id,
    "ancestor_ids": ancestor_ids.copy(),
    # Add custom fields here
    "my_custom_field": node.get("custom", "")
}
```

**Note**: S3 Vectors metadata has size limits. Keep metadata concise.

### Batch Size Tuning

Adjust for your workload:

```python
EMBEDDING_BATCH_SIZE = 25      # Bedrock call size
MAX_VECTORS_PER_UPLOAD = 50    # S3 Vectors call size
```

Higher values = faster but less granular error handling.

## Testing

### Integration Testing
```bash
# Full pipeline test
python3 skill-embeddings.py

# Verify output
python3 test-skill-embeddings.py
```
