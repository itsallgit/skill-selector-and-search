# Deployment

## Infrastructure Setup

### Deploy Command

```bash
cd skill-selector/infra
./deploy-skill-selector.sh
```

### What Gets Created

1. **S3 Bucket**
   - Name: `skills-selector-{timestamp}`
   - Region: Based off AWS profile selected
   - Versioning: Disabled
   - Public Access: Configured for static hosting

### First Time Deployment

Typically takes 2-3 minutes:
- Creating AWS resources
- Uploading skills-master.json
- Configuring frontend files
- Uploading HTML/CSS/JS

### Subsequent Deployments

Much faster (seconds):
- Resources already exist
- Only uploads changed files
- Preserves existing user profiles

## Update Workflows

### Update Skills Taxonomy

When `skills-master.json` changes:

```bash
cd skill-selector/infra
./deploy-skill-selector.sh
```

The script:
- Detects existing bucket
- Uploads new skills-master.json
- Preserves all user profiles
- No downtime

### Update Frontend Code

When HTML/CSS/JS changes:

```bash
cd skill-selector/infra
./deploy-skill-selector.sh
```

Or manually:
```bash
aws s3 cp frontend/index.html s3://{bucket}/ --profile your-profile
aws s3 cp frontend/app.js s3://{bucket}/ --profile your-profile
aws s3 cp frontend/styles.css s3://{bucket}/ --profile your-profile
```

### Manual Backup

Before deploying:
```bash
# Backup current state
aws s3 sync s3://{bucket}/ ./backup-$(date +%Y%m%d)/
```

To rollback:
```bash
# Restore from backup
aws s3 sync ./backup-{date}/ s3://{bucket}/
```
