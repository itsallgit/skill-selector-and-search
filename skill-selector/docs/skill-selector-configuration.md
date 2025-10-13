# Configuration

Configuration is embedded in `frontend/app.js` and set during deployment.

## AWS Configuration

These values are automatically configured by `deploy-skill-selector.sh`:

```javascript
// AWS Configuration
const AWS_REGION = 'ap-southeast-2';
const BUCKET_NAME = 'skills-selector-1760061975';
```

**After deployment**, the script updates `app.js` with the correct values.

## Manual Configuration (if needed)

If you need to update configuration manually:

1. **Open** `frontend/app.js`
2. **Find** the AWS Configuration section (near top of file)
3. **Update** these constants:
   - `AWS_REGION`: Your AWS region
   - `IDENTITY_POOL_ID`: From Cognito console
   - `BUCKET_NAME`: Your S3 bucket name

## S3 File Paths

Default file locations in the S3 bucket:

```javascript
const SKILLS_MASTER_KEY = 'skills-master.json';
const USERS_FOLDER = 'users/';
const USERS_MASTER_KEY = 'users-master.json';
```

**To change paths**: Update these constants in `app.js`.

## UI Customization

### Skill Ratings

Rating options are defined in the code:

```javascript
const ratings = [
    { value: 1, label: 'Beginner' },
    { value: 2, label: 'Intermediate' },
    { value: 3, label: 'Advanced' }
];
```

**To add levels**: Update the ratings array and corresponding CSS.

## Styling

The application uses `shared/styles.css` for consistency with skill-search.

**Custom styles**: Add to `frontend/styles.css` (component-specific overrides).

