# Overview

Generates semantic embeddings for skills and uploads them to an AWS S3 Vector Index for semantic search capabilities.

## Key Capabilities

- **Hierarchical Skill Processing**: Flattens skills-master.json structure into searchable vectors
- **Incremental Updates**: Detects changes and only generates embeddings for new/modified skills
- **AWS Bedrock Integration**: Uses Titan Embeddings V2 for high-quality semantic representations
- **Batch Processing**: Efficient API usage with configurable batch sizes
- **S3 Vector Index**: Uploads to AWS S3 Vectors for fast semantic search
- **Rich Metadata**: Preserves skill hierarchy, titles, and relationships

## What It Does

The skill embeddings generator transforms hierarchical skill data into semantic vectors:

1. **Reads** `skills-master.json` (hierarchical structure)
2. **Flattens** skills with preserved hierarchy metadata
3. **Detects** changes by comparing with existing embeddings
4. **Generates** embeddings only for new/changed skills (saves cost)
5. **Saves** to `skill-embeddings.jsonl` (persistent storage)
6. **Uploads** all vectors to S3 Vector Index

Each skill becomes a searchable vector with metadata including title, level, parent relationships, and full ancestry chain.
