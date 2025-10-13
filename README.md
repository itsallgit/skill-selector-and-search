# Skill Selector and Search

A comprehensive solution for skill management, assessment, and discovery powered by AWS Bedrock and semantic search technologies.

## Components

### 1. Skill Selector
An interactive web application for users to self-assess their skills across a hierarchical taxonomy. Users can rate their proficiency levels and save their skill profiles.

📖 [Read more](skill-selector/README-skill-selector.md)

### 2. Skill Embeddings
Generates semantic embeddings for hierarchical skills using AWS Bedrock and uploads them to AWS S3 Vector Index for semantic search capabilities.

📖 [Read more](skill-embeddings/README-skill-embeddings.md)

### 3. Skill Search
A full-stack web application for finding users by skills using natural language semantic search. Features intelligent ranking algorithms and real-time search capabilities.

📖 [Read more](skill-search/README-skill-search.md)

## Getting Started

The easiest way to set up and deploy the project is using the interactive setup script:

```bash
./project-setup.sh
```

This script provides a menu-driven interface to:
- Deploy individual components
- Configure AWS resources
- Manage the entire solution lifecycle

Follow the on-screen prompts to deploy the components you need.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with profiles
- Python 3.8+ (for embeddings and search backend)
- Node.js 14+ (for search frontend)
- Docker (for skill search deployment)

For detailed prerequisites and configuration for each component, refer to their respective README files.
