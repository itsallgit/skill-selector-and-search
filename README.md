# Skills Selector Application

A modern, responsive single-page application (SPA) for selecting and managing professional skills. Built to run on AWS S3 with public file access, this application provides a hierarchical skill selection interface with persistent storage.

## Features

- **User Management**: Email-based user registration and profile management
- **Hierarchical Skills**: Three-level skill structure (Categories → Sub-categories → Individual Skills)
- **Interactive UI**: Modern, responsive design with responsive grid layout
- **Persistent Storage**: User selections saved to S3 under `users/<email>-<timestamp>.json`
- **Returning Users**: Automatic loading of previously selected skills (latest saved file referenced in `users-master.json`)
- **Real-time Updates**: Dynamic skill exploration with live selection counts
- **Selection Grouping**: Selected skills displayed grouped by Level 1 and Level 2 for readability
- **Selection Indicators**: L3 skills show a “Selected” badge; L1/L2 tiles show aggregated selected counts
- **Users Directory Page**: Dedicated `users.html` renders total user count and per-user selected skill counts
- **Scroll Assist**: “View Selected Skills” button in explorer footer scrolls back to selection summary
- **Zero Dependencies**: Pure HTML/CSS/JS (no build step required)

## Application Structure

### Skill Hierarchy
- **Level 1 (L01)**: Primary skill categories (e.g., Technology Consulting, Business Process Consulting)
- **Level 2 (L02)**: Sub-categories within each primary area (e.g., Digital Strategy, Cloud Solutions)
- **Level 3 (L03)**: Individual, selectable skills (e.g., Digital Transformation Planning, Cloud Migration Strategy)

### File Structure
```
/
├── index.html              # Main application shell (skill explorer & selection UI)
├── users.html              # Users listing (counts of selected skills)
├── styles.css              # Application styles (includes navbar, grouping, badges)
├── app.js                  # Core application logic
├── skills-master.json      # Master skills hierarchical data
├── users-master.json       # User registry (email, skillsFile pointer, timestamps)
├── deploy.sh               # AWS deployment automation
└── README.md               # Documentation
```

## Getting Started

### Prerequisites

1. **AWS CLI**: Install and configure the AWS CLI
   ```bash
   # macOS
   brew install awscli
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install awscli
   
   # Linux (CentOS/RHEL)
   sudo yum install awscli
   ```

2. **AWS Configuration**: Configure your AWS credentials
   ```bash
   aws configure
   ```
   
   You'll need:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (ap-southeast-2 for Sydney)
   - Output format (json)

### Deployment

1. **Clone/Download** this repository to your local machine

2. **Review Configuration**: Edit `deploy.sh` if needed to customize:
   - Bucket name (auto-generated with timestamp by default)
   - AWS region (set to Sydney/ap-southeast-2)
   - AWS profile

3. **Deploy to AWS**:
   ```bash
   # Make the script executable (if not already)
   chmod +x deploy.sh
   
   # Run the deployment
   ./deploy.sh
   ```

### Deployment Script Features

The deployment script (`deploy.sh`) is **idempotent** and handles:

- **AWS CLI Verification**: Checks if AWS CLI is installed and configured
- **Bucket Creation**: Creates S3 bucket if it doesn't exist
- **Static Website Hosting**: Configures bucket for web hosting
- **CORS Configuration**: Sets up Cross-Origin Resource Sharing for file operations
- **Public Access**: Configures bucket policy for public read access
- **File Upload**: Uploads all application files to S3
- **Success Reporting**: Provides the final application URL

### Post-Deployment

After successful deployment, you'll receive:
- **Application URL**: Direct link to your hosted application
- **Bucket Information**: S3 bucket details and configuration

## Usage

### For End Users

1. **Access Application**: Navigate to the provided S3 website URL
2. **Enter Email**: Provide your email address to create/access your profile
3. **Explore Skills**: Navigate through the three-level skill hierarchy:
   - Click on Level 1 categories to see sub-categories
   - Click on Level 2 sub-categories to see individual skills
   - Click on Level 3 skills to select/deselect them
4. **Review Selections**: View selected skills in the "Selected Skills" section
5. **View Selected**: Use the “View Selected Skills” footer button to jump back up when browsing
6. **Save Progress**: Click "Save Skills" to persist your selections (creates a timestamped JSON in `users/`)
7. **Return Later**: Use the same email to reload your previous selections
8. **Users Overview**: Open Menu → Users to view all registered users and skill counts

### For Administrators

#### Updating Skills

Edit `skills-master.json` to modify the skill database. The file uses a nested structure:

```json
{
  "L01S001": {
    "title": "Category Name",
    "description": "Category description",
    "skills": {
      "L02S001": {
        "title": "Sub-category Name", 
        "description": "Sub-category description",
        "skills": {
          "L03S001": {
            "title": "Individual Skill",
            "description": "Skill description"
          }
        }
      }
    }
  }
}
```

**ID Conventions**:
- L01S### for Level 1 skills
- L02S### for Level 2 skills  
- L03S### for Level 3 skills

#### Re-deploying Changes

After modifying skills:
```bash
./deploy.sh
```

The script will update only changed files.

## Architecture

### Client-Side Application
- **HTML5**: Semantic markup with accessibility considerations
- **CSS3**: Modern styling with flexbox/grid, animations, and responsive design
- **Vanilla JavaScript**: No external dependencies, ES6+ features

### AWS Infrastructure
- **S3 Static Hosting**: Serves HTML, CSS, JS files
- **S3 Object Storage**: Stores JSON data files
- **CloudFront** (optional): Can be added for global CDN

### Data Flow
1. User enters email → App fetches `users-master.json` (or creates new entry)
2. If user has `skillsFile`, fetch latest user skills JSON and hydrate selections
3. Master hierarchy loaded from `skills-master.json`
4. User selects L3 items; counts for parent L1/L2 update live
5. Save generates `users/<email>-<timestamp>.json` via direct S3 PUT and updates `users-master.json`
6. Selected skills panel renders grouped by L1 → L2 → L3
7. Users page (`users.html`) enumerates users and counts L3 selections by reading their referenced file

## Security Considerations

⚠️ **Important**: Intended for **public / low-sensitivity data**.

- Bucket policy currently allows public read (and may allow write if configured for direct PUT). This should be restricted for production by introducing an authenticated API or signed URLs.
- Email addresses stored in plain text within `users-master.json`.
- Consider enabling S3 Object Ownership & restricting public write access.
- Add rate limiting / validation server-side if moving beyond prototype.

## Browser Compatibility

- **Modern Browsers**: Chrome 60+, Firefox 60+, Safari 12+, Edge 79+
- **Mobile**: iOS Safari 12+, Chrome Android 60+
- **Features Used**: Fetch API, ES6 classes, CSS Grid/Flexbox

## Customization

### Styling
Edit `styles.css` to customize:
- Color scheme (currently white/black/green)
- Typography and spacing
- Component layouts
- Responsive breakpoints

### Behavior
Edit `app.js` to modify:
- Skill selection logic
- Navigation behavior
- Error handling
- API interaction patterns

### Content
Edit `skills-master.json` to:
- Add/remove skill categories
- Modify descriptions
- Reorganize hierarchy
