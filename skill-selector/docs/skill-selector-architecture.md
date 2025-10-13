# Architecture

## Technology Stack

- **Frontend**: Pure HTML5, CSS3, JavaScript (no framework)
- **Storage**: AWS S3 for master data and user profiles
- **Deployment**: Static hosting (S3)

## Component Structure

### Static Assets
- **index.html**: Main skill selection interface
- **users.html**: User management and profile viewing
- **app.js**: Application logic and AWS integration
- **styles.css**: Shared styling with skill-search

### Data Flow

```
User Browser
    ↓
[Load skills-master.json from S3]
    ↓
[User selects skills + ratings]
    ↓
[Generate user profile JSON]
    ↓
[Upload to S3: users/{email}.json]
```

## AWS Integration

### S3 Bucket Structure
```
skills-selector-{timestamp}/
├── skills-master.json       # Hierarchical skill taxonomy
├── users-master.json        # Consolidated user profiles (generated)
└── users/                   # Individual user profiles
    ├── user1@example.com.json
    ├── user2@example.com.json
    └── ...
```

## Hierarchical Skill Model

Skills are organized in 4 levels:

- **L1 (Categories)**: Broad domains (e.g., "Cloud Computing")
- **L2 (Sub-categories)**: Major areas (e.g., "Compute Services")
- **L3 (Generic Skills)**: Transferable competencies (e.g., "Serverless Architecture")
- **L4 (Technologies)**: Specific tools (e.g., "AWS Lambda")

Users can select skills at any level. The hierarchy provides context for semantic search and skill matching.

## Stateless Design

The application is completely stateless:
- No server-side sessions
- No databases
- All state in browser memory
- All persistence via S3
- Can be deployed as static files anywhere

**Benefits**:
- Simple deployment
- No maintenance overhead
- Infinite scalability
- Cost-effective
