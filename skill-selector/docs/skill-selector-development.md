# Development

## Project Structure

```
skill-selector/
├── frontend/
│   ├── index.html      # Main skill selection interface
│   ├── users.html      # User management interface
│   ├── app.js          # Application logic
│   └── styles.css      # Component-specific styles
├── infra/
│   └── deploy-skill-selector.sh  # Deployment script
└── docs/               # This documentation
```

## Local Development

### Running Locally

The application can run from local filesystem:

```bash
cd skill-selector/frontend
open index.html  # macOS
# or
xdg-open index.html  # Linux
# or
start index.html  # Windows
```

**Limitations**:
- S3 access requires valid AWS configuration in `app.js`
- CORS may prevent some operations
- Best to test against deployed S3 instance

## Extending the Application

### Adding Skill Levels

To add more rating levels:

1. **Update ratings array** in `app.js`:
   ```javascript
   const ratings = [
       { value: 1, label: 'Beginner' },
       { value: 2, label: 'Intermediate' },
       { value: 3, label: 'Advanced' },
       { value: 4, label: 'Expert' }  // NEW
   ];
   ```

2. **Update CSS** if needed for styling

3. **Update backend** (skill-search) rating multipliers
