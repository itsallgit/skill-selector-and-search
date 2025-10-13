# Deployment

## Infrastructure Deployment

### Create Vector Index

```bash
cd skill-embeddings/infra
./deploy-skill-embeddings.sh
```

The script will:
1. Prompt for AWS profile selection
2. Generate unique bucket name with timestamp
3. Create S3 Vector Bucket (if needed)
4. Create Vector Index with:
   - Dimension: 1024
   - Distance Metric: Cosine
   - Name: skills-index

**Save the output**: You'll need the bucket name for configuration.

### One-Time Setup

Infrastructure deployment is typically one-time unless:
- Changing AWS regions
- Modifying distance metric
- Changing embedding dimensions
- Setting up new environment (dev/staging/prod)

## Generate and Upload Embeddings

### Initial Population

```bash
cd skill-embeddings/scripts

# 1. Update configuration
# Edit skill-embeddings.py with your VECTOR_BUCKET value

# 2. Run generator
python3 skill-embeddings.py
```

**First run** will:
- Generate embeddings for all skills
- Save to skill-embeddings.jsonl
- Upload all vectors to index
- Take several minutes (depends on skill count)

### Incremental Updates

When skills-master.json changes:

```bash
cd skill-embeddings/scripts
python3 skill-embeddings.py
```

**Subsequent runs**:
- Only process new/changed skills
- Update existing embeddings
- Re-upload full dataset to index
- Much faster than initial run

### Monitoring

**Key Metrics**:
- Embedding generation time
- Vector upload success rate
- Index size and growth
- API error rates

**Validation**:
```bash
# After deployment
cd scripts
python3 test-skill-embeddings.py
```

Perform test searches to verify:
- Vector index accessible
- Search results relevant
- Similarity scores reasonable

### Backup and Recovery

**Backup Embeddings**:
```bash
# skill-embeddings.jsonl is your backup
cp ../../data/skill-embeddings.jsonl ../../data/skill-embeddings-backup-$(date +%Y%m%d).jsonl
```

**Disaster Recovery**:
1. Restore skill-embeddings.jsonl from backup
2. Re-run deployment script (creates infrastructure)
3. Run skill-embeddings.py (uploads from JSONL)
4. Verify with test script
