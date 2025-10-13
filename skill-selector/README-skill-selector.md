# Skill Selector

An interactive web application for users to self-assess their skills across a hierarchical taxonomy.

## Documentation

- [Overview](docs/skill-selector-overview.md) - What it does and key capabilities
- [Architecture](docs/skill-selector-architecture.md) - Technology stack and AWS integration
- [Prerequisites](docs/skill-selector-prerequisites.md) - Required software and AWS access
- [Configuration](docs/skill-selector-configuration.md) - AWS settings and customization
- [Quick Start](docs/skill-selector-quick-start.md) - Deploy and start using
- [Development](docs/skill-selector-development.md) - Local development and code structure
- [Implementation](docs/skill-selector-implementation.md) - Technical details and algorithms
- [Deployment](docs/skill-selector-deployment.md) - Infrastructure and hosting options

## Quick Reference

```bash
# Deploy infrastructure and application
cd infra && ./deploy-skill-selector.sh

# Access application (URL from deployment output)
open https://skills-selector-*.s3.ap-southeast-2.amazonaws.com/index.html

# Update skills taxonomy
aws s3 cp ../../data/skills-master.json s3://skills-selector-*/
```

## What It Does

Provides an intuitive interface for users to:
1. **Enter** their email to start a session
2. **Navigate** a 4-level skill hierarchy (L1-L4)
3. **Select** relevant skills at any level
4. **Rate** their proficiency (Beginner, Intermediate, Advanced)
5. **Save** their profile to S3

Profiles are immediately available for semantic search queries in the Skill Search application.

## User Flow

**For Users**:
- Open application URL
- Enter email address
- Browse and select skills
- Rate each selected skill
- Save profile

**For Administrators**:
- Navigate to users.html
- View all user profiles
- Edit existing profiles
- Manage skill data

## Technology

- **Pure Frontend**: No backend server required
- **AWS S3**: Static hosting and data storage

