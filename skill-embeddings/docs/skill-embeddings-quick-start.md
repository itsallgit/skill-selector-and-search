# Quick Start

## Initial Setup

1. **Deploy Vector Infrastructure**:
   
   From the project menu:
   - Main Menu → Skill Embeddings → Provision Vector Bucket & Index
   
   Or via command line:
   ```bash
   cd skill-embeddings/infra
   ./deploy-skill-embeddings.sh
   ```
   
   This creates:
   - S3 Vector Bucket
   - Vector Index with cosine distance metric

2. **Configure and Run Embeddings**:
   
   From the project menu:
   - Main Menu → Skill Embeddings → Setup & Run Embeddings
   
   Or via command line:
   ```bash
   cd skill-embeddings
   ./skill-embeddings-setup.sh
   ```
   
   The setup script will:
   - List available AWS profiles
   - Prompt for profile selection
   - List available vector buckets
   - Generate configuration file
   - Provide menu to generate or test embeddings

## Generate Embeddings

After configuration, select "Generate Skill Embeddings" from the operations menu.

Or run directly:
```bash
cd skill-embeddings/scripts
python3 skill-embeddings.py
```

**First run** generates embeddings for all skills (takes several minutes depending on skill count).

**Subsequent runs** only process new/changed skills (much faster).

## What to Expect

The script will:
1. ✓ Load configuration from skill-embeddings-config.json
2. ✓ Connect to AWS Bedrock and S3 Vectors
3. ✓ Verify vector index exists
4. ✓ Load and flatten skills-master.json
5. ✓ Compare with existing embeddings
6. ✓ Generate embeddings for delta (or all if first run)
7. ✓ Save to skill-embeddings.jsonl
8. ✓ Upload all vectors to S3 index
9. ✓ Show summary statistics

## Verify Success

```bash
# Check embeddings file was created
ls -lh ../../data/skill-embeddings.jsonl

# Count embeddings
wc -l ../../data/skill-embeddings.jsonl

# Test search capability
python3 test-skill-embeddings.py
```

The test script lets you perform semantic searches to verify embeddings work correctly.

## When to Re-run

Run the embeddings generator when:
- Skills-master.json is updated (new/changed skills)
- Skill descriptions are modified
- You want to switch embedding models
- Vector index is recreated

The incremental update feature makes frequent re-runs efficient.
