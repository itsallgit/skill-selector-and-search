# Implementation

## Scoring Algorithm

The scoring algorithm ranks users based on multiple factors to provide intelligent, contextual search results.

### Design Rationale

The algorithm balances three key considerations:
1. **Semantic Relevance**: How closely skills match the query (vector similarity)
2. **Skill Importance**: Hierarchy level matters (L3 generic skills > L4 tools)
3. **User Proficiency**: Advanced users should rank higher for matched skills

### 1. Level Weights

How much each skill hierarchy level contributes to the score:
- **L1 (Categories)**: 0.1 - Very broad, minimal weight
- **L2 (Sub-categories)**: 0.2 - Broader context
- **L3 (Generic Skills)**: 0.5 - **MOST IMPORTANT** - Core competencies
- **L4 (Technologies)**: 0.3 - Specific tools/tech

**Rationale**: L3 skills represent transferable competencies (e.g., "Container Orchestration") while L4 are specific implementations (e.g., "Kubernetes"). Prioritizing L3 ensures we find users with the right conceptual knowledge, not just tool experience.

### 2. Rating Multipliers (Exponential)

User's self-assessed proficiency level:
- **Beginner (1)**: 1.0x
- **Intermediate (2)**: 2.0x
- **Advanced (3)**: 4.0x

**Rationale**: Advanced users with relevant L3 skills should rank higher than Intermediate users even if the latter have more specific L4 tool matches. The exponential scale reflects the non-linear growth in competency.

### 3. Similarity Score

From vector search (0-1 scale):
- Derived from cosine distance: `similarity = 1 - distance`
- Measures how semantically close the skill is to the query

Lower cosine distance = higher similarity = better match.

### 4. Transfer Bonus

Partial credit for related technology experience:
- If query matches an L3 skill, but user only has the L4 technology under a **different** L3, they get partial credit
- **Example**: 
  - Query matches: "Serverless Architecture (L3) > AWS Lambda (L4)"
  - User has: "Cloud Security (L3) > AWS Lambda (L4)"
  - → User gets transfer bonus for AWS Lambda competence
- **Bonus**: 0.02 per transferable technology, capped at 0.15 (15%)

**Rationale**: Technology experience often transfers across domains. Someone with AWS Lambda experience in security can apply that knowledge to serverless architecture projects.

### Formula

For each matched skill:
```
base_score = similarity × level_weight × rating_multiplier
```

User total score:
```
raw_score = Σ(base_score for all matched skills) + transfer_bonus
normalized_score = (raw_score / max_possible_score) × 100
```

### Ranking Example

Query: "Container Orchestration (L3) + Kubernetes (L4)"

1. **User C**: Has Kubernetes (L4) under Container Orchestration (L3)
   - Direct L3 + L4 match = **HIGHEST** score
   - Gets full weight for both hierarchy levels

2. **User B**: Has Docker (L4) under Container Orchestration (L3)
   - Direct L3 match + different L4 = **HIGH** score
   - Strong L3 match compensates for different L4 tool

3. **User A**: Has Kubernetes (L4) under DevOps (different L3)
   - No L3 match, but gets transfer bonus = **MEDIUM** score
   - Ranks above users with NO relevant skills
   - Kubernetes experience recognized even in different context

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
