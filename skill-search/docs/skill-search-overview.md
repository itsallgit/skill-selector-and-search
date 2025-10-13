# Overview

A full-stack web application for finding users by skills using natural language semantic search.

## Key Capabilities

- **Natural Language Search**: Enter queries like "AWS Lambda and serverless architecture" to find relevant users
- **Vector-based Matching**: Uses AWS Bedrock Titan Embeddings V2 for semantic skill matching
- **Smart Ranking Algorithm**: 
  - Weighted scoring across skill hierarchy levels (L1-L4)
  - Exponential rating multipliers for user proficiency
  - Transfer bonus for related technologies under different categories
- **Intuitive UI**:
  - Top 5 matches always displayed
  - Expandable score buckets (Excellent, Strong, Good, Other)
  - User detail pages with full skill breakdown
- **Docker Deployment**: One-click setup with `./skill-search-setup.sh`
