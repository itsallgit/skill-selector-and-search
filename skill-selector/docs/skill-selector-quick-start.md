# Quick Start

## Deploy Infrastructure and Application

```bash
cd skill-selector/infra
./deploy-skill-selector.sh
```

**What the script does:**
1. ✓ Prompts for AWS profile selection
2. ✓ Creates S3 bucket with unique name
5. ✓ Uploads skills-master.json
6. ✓ Configures and uploads frontend files
7. ✓ Shows you the S3 URL to access the application

**First-time setup** takes 2-3 minutes.

## Access the Application

After deployment, the script shows:

```
Application deployed successfully!
Access URL: https://skills-selector-1760061975.s3.ap-southeast-2.amazonaws.com/index.html
```

Open this URL in your browser.

## Using the Application

### For Users (Skill Selection)

1. **Open** the application URL
2. **Enter** your email address
3. **Navigate** the skill tree (click to expand categories)
4. **Select** relevant skills (checkboxes)
5. **Rate** your proficiency for each skill
6. **Save** your profile

Your profile is immediately available for skill search queries.

## Testing

Verify deployment:

```bash
# Check S3 bucket exists
aws s3 ls s3://skills-selector-* --profile your-profile

# Verify skills-master.json uploaded
aws s3 ls s3://skills-selector-*/skills-master.json --profile your-profile

# Test file access
curl https://skills-selector-*.s3.ap-southeast-2.amazonaws.com/skills-master.json
```

## Updating Skills

When `skills-master.json` changes:

```bash
cd skill-selector/infra
./deploy-skill-selector.sh
```

The script:
- Uses existing bucket
- Uploads new skills-master.json
- Preserves user profiles
- Updates frontend if needed

Users will see updated skills on next page reload.
