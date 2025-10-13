# Overview

An interactive web application for users to self-assess their skills across a hierarchical taxonomy.

## Key Capabilities

- **Email-Based Sessions**: Simple email entry to begin skill selection
- **Hierarchical Skill Tree**: Navigate 4-level skill taxonomy (L1-L4)
- **Self-Assessment Ratings**: Rate proficiency (Beginner, Intermediate, Advanced)
- **Real-Time Validation**: Ensures complete and valid selections
- **S3 Persistence**: Saves user profiles to AWS S3 bucket
- **User Management**: View and manage existing user profiles
- **Static Deployment**: Pure frontend - no backend server required

## What It Does

The skill selector provides an intuitive interface for users to:

1. **Enter** their email address to start
2. **Navigate** the hierarchical skill tree
3. **Select** relevant skills at any level (L1-L4)
4. **Rate** their proficiency for each selected skill
5. **Save** their profile to S3 storage

The application generates a JSON profile that includes:
- User email
- Selected skills with ratings
- Skill hierarchy metadata
- Timestamp information

These profiles are then used by the Skill Search application to find matching consultants.
