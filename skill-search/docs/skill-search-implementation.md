# Implementation

## Scoring Algorithm

The scoring algorithm uses a **two-dimensional approach** to rank users based on both skill breadth (Coverage) and skill depth (Expertise).

### Design Rationale

The algorithm balances two key dimensions:
1. **Coverage (Breadth)**: How many relevant skills the user possesses
2. **Expertise (Depth)**: The proficiency level across those matched skills

This ensures that users with deep expertise in highly relevant skills rank appropriately compared to users with many weakly relevant skills.

### Dimension 1: Coverage

**Coverage** measures the breadth and strength of skill matches against the query.

**Formula**:
```python
coverage = Σ(similarity²) for all matched skills
```

**How It Works**:
- Each matched skill contributes based on its semantic similarity to the query
- Similarity values range from 0.0 to 1.0 (from vector search cosine distance)
- Squaring the similarity emphasizes stronger matches while still giving credit to weaker ones
- Higher coverage = more relevant skills = better breadth

**Example**:
- Query: "AWS Lambda and serverless architecture"
- User has 3 matched skills:
  - AWS Lambda: similarity = 0.95 → contributes 0.9025
  - Serverless Architecture: similarity = 0.88 → contributes 0.7744
  - API Gateway: similarity = 0.75 → contributes 0.5625
- Total coverage = 0.9025 + 0.7744 + 0.5625 = 2.2394

**Display**: Coverage is shown as a percentage relative to maximum possible coverage:
```python
coverage_percentage = (coverage / max_possible_coverage) × 100
```

### Dimension 2: Expertise

**Expertise** measures the average proficiency level across matched skills.

**Formula**:
```python
expertise = Σ(similarity² × rating_multiplier) / Σ(similarity²)
```

**Rating Multipliers**:
- **Beginner (1)**: 1.0× multiplier
- **Intermediate (2)**: 3.0× multiplier  
- **Advanced (3)**: 6.0× multiplier

**Rationale**: The exponential scale (1.0, 3.0, 6.0) reflects the non-linear growth in competency. An Advanced user's expertise is worth significantly more than an Intermediate user's.

**Expertise Labels**:
- 5.0+ → **Expert**
- 3.5-4.9 → **Advanced**
- 2.0-3.4 → **Intermediate**
- 1.3-1.9 → **Early Career**
- < 1.3 → **Beginner**

**Example**:
Using the same 3 matched skills from above:
- AWS Lambda (similarity² = 0.9025, rating = 3): 0.9025 × 6.0 = 5.415
- Serverless Architecture (similarity² = 0.7744, rating = 2): 0.7744 × 3.0 = 2.323
- API Gateway (similarity² = 0.5625, rating = 3): 0.5625 × 6.0 = 3.375
- Total weighted = 11.113
- Total weight = 2.2394
- Expertise = 11.113 / 2.2394 = 4.96 → **Advanced**

### Final Ranking

**Raw Score** = Coverage × Expertise

This raw score is used for ranking users. Higher values indicate better matches overall.

**Example**:
- Coverage = 2.2394
- Expertise = 4.96
- Raw Score = 2.2394 × 4.96 = 11.107

**Display Score**: For the UI, scores are normalized so the top user = 100:
```python
display_score = (user_raw_score / top_user_raw_score) × 100
```

### Ranking Scenarios

**Scenario 1: Breadth vs. Depth**
- **User A**: 10 matched skills, average expertise = 2.5 (Intermediate)
  - Coverage = 5.0, Expertise = 2.5, Raw Score = 12.5
- **User B**: 3 matched skills, average expertise = 5.5 (Expert)
  - Coverage = 2.8, Expertise = 5.5, Raw Score = 15.4
- **Result**: User B ranks higher (deeper expertise wins)

**Scenario 2: High Relevance Wins**
- **User C**: 1 perfect match (similarity = 0.95, rating = 3)
  - Coverage = 0.9025, Expertise = 6.0, Raw Score = 5.42
- **User D**: 5 weak matches (average similarity = 0.6, rating = 3)
  - Coverage = 1.8, Expertise = 6.0, Raw Score = 10.8
- **Result**: User D ranks higher (more coverage, same expertise)

**Scenario 3: Balanced Match**
- **User E**: 5 strong matches (average similarity = 0.85), mix of Advanced and Intermediate ratings
  - Coverage = 3.6, Expertise = 4.2, Raw Score = 15.12
- **Result**: Balanced approach to coverage and expertise often performs best

## API Endpoints

### Search Users
```http
POST /api/search
Content-Type: application/json

{
  "query": "AWS Lambda and serverless architecture",
  "top_k_skills": 10,
  "top_n_users": 5
}
```

**Response**: Matched skills, top users, and score buckets

**Implementation Details**:
1. Generate embedding for query using AWS Bedrock Titan V2
2. Query S3 Vector index for top K similar skills
3. Find users with matched skills
4. Calculate scores using algorithm above
5. Group users into score buckets
6. Return ranked results

### Get User Detail
```http
GET /api/users/{email}
```

**Response**: User details with full skill breakdown

**Implementation Details**:
- Retrieves user from in-memory repository
- Expands skill IDs to full skill details
- Returns complete profile with all skills organized by hierarchy

### Health Check
```http
GET /api/health
```

**Response**: Service status and user count

**Implementation Details**:
- Checks user repository is loaded
- Returns basic statistics
- Used for monitoring and container health checks

### Statistics
```http
GET /api/stats
```

**Response**: Application statistics and configuration

**Implementation Details**:
- Returns user count, skill counts by level
- Shows active configuration (AWS profiles, weights, etc.)
- Useful for debugging and validation

## Vector Search Implementation

The application uses AWS S3 Vectors for efficient semantic search:

1. **Index Structure**: Pre-built index with 1024-dimensional embeddings
2. **Distance Metric**: Cosine distance (lower = more similar)
3. **Metadata**: Each vector includes skill ID, title, level, hierarchy info
4. **Query Flow**:
   - Generate query embedding via Bedrock
   - Query index with `topK` parameter
   - Receive ranked results with distances and metadata
   - Convert distances to similarity scores (1 - distance)

## Data Repository Pattern

The backend uses a repository pattern for data access:

**Benefits**:
- Abstracts data storage implementation
- Currently uses in-memory JSON for speed
- Can migrate to database without changing business logic
- Supports caching and performance optimization

**Current Implementation**:
- Loads `user_db.json` at startup
- Keeps data in memory for fast access
- Indexed by email for O(1) lookups
- Regenerated via `ingest_users.py` script
