# Architecture

## Components

### Input Data
- **skills-master.json**: Hierarchical skill taxonomy (4 levels: L1-L4)
- **skill-embeddings.jsonl**: Previously generated embeddings (for incremental updates)

### Processing Pipeline

1. **Skill Flattening**: Converts hierarchy to flat list with preserved relationships
2. **Change Detection**: Compares with existing embeddings to identify delta
3. **Embedding Generation**: Uses AWS Bedrock Titan V2 (1024 dimensions)
4. **Persistence**: Saves to JSONL format for future incremental runs
5. **Vector Upload**: Batch uploads to S3 Vector Index

### AWS Services

- **AWS Bedrock**: Generate embeddings (typically us-east-1)
  - Model: `amazon.titan-embed-text-v2:0`
  - Dimensions: 1024
  - Normalized: Yes
  
- **AWS S3 Vectors**: Store and query vector index
  - Distance Metric: Cosine
  - Supports metadata queries
  - Fast similarity search

## Data Flow

```
skills-master.json (hierarchical)
    ↓
[Flatten] → Flat skill list with metadata
    ↓
[Compare] → Identify new/changed skills
    ↓
[Generate] → AWS Bedrock Titan V2 embeddings
    ↓
[Save] → skill-embeddings.jsonl
    ↓
[Upload] → S3 Vector Index
```

## Multi-Account Support

Like the skill-search application, this script supports multi-account AWS setups:
- **Bedrock Account**: Access to embedding model
- **S3 Vectors Account**: Access to vector bucket and index

Configure via profiles at the top of `skill-embeddings.py`.
