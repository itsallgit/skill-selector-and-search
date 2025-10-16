# Overview

A full-stack web application for finding users by skills using natural language semantic search.

## Key Capabilities

- **Natural Language Search**: Enter queries like "AWS Lambda and serverless architecture" to find relevant users
- **Vector-based Matching**: Uses AWS Bedrock Titan Embeddings V2 for semantic skill matching
- **Two-Dimensional Ranking Algorithm**: 
  - **Coverage** (Breadth): Measures relevant skills matched (Σ similarity²)
  - **Expertise** (Depth): Measures proficiency level (weighted average with 1.0×, 3.0×, 6.0× multipliers)
  - Final ranking = Coverage × Expertise
- **Intuitive UI**:
  - Top 5 matches always displayed
  - Prominent visual display of Coverage and Expertise dimensions
  - Expandable score buckets (Excellent, Strong, Good, Other)
  - User detail pages with full skill breakdown
- **Docker Deployment**: One-click setup with `./skill-search-setup.sh`
