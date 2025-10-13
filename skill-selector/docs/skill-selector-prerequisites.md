# Prerequisites

## Required Data
- `data/skills-master.json` - Hierarchical skill taxonomy

## AWS Requirements

### S3 Bucket
- Created via `deploy-skill-selector.sh`
- Stores skills-master.json and user profiles
- Public read access for skills-master.json
- Write access for user profiles (via Cognito)

## AWS Permissions

Your AWS profile (for deployment) needs:
- `s3:CreateBucket` - Create S3 bucket
- `s3:PutObject` - Upload files
- `s3:PutBucketPolicy` - Configure access
