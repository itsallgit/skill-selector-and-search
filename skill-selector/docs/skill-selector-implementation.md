# Implementation

## Skill Tree Rendering

### Design Rationale

The hierarchical skill tree is rendered recursively to handle arbitrary nesting depths while maintaining performance.

### Recursive Algorithm

```javascript
function buildSkillTree(skills, parentElement, level = 1) {
    skills.forEach(skill => {
        // Create container
        const container = document.createElement('div');
        container.className = `skill-level-${level}`;
        
        // Add checkbox and label
        const checkbox = createCheckbox(skill);
        const label = createLabel(skill);
        
        // Add rating dropdown (hidden until selected)
        const ratingDropdown = createRatingDropdown(skill);
        
        container.appendChild(checkbox);
        container.appendChild(label);
        container.appendChild(ratingDropdown);
        
        // Recursively handle children
        if (skill.skills && skill.skills.length > 0) {
            const childContainer = document.createElement('div');
            childContainer.className = 'skill-children collapsed';
            buildSkillTree(skill.skills, childContainer, level + 1);
            container.appendChild(childContainer);
        }
        
        parentElement.appendChild(container);
    });
}
```

**Benefits**:
- Handles any hierarchy depth
- Clean separation of concerns
- Easy to extend with new features
- Efficient DOM manipulation

## State Management

### Application State

```javascript
// Global state object
const state = {
    user: {
        email: null,
        selectedSkills: [],
        ratings: {}
    },
    ui: {
        currentView: 'email',
        expandedNodes: [],
        isDirty: false
    },
    data: {
        skillsTree: null,
        skillsFlat: null
    }
};
```

**State Updates**: Centralized via helper functions to maintain consistency.

### Skill Selection State

When user selects a skill:
1. Add to `selectedSkills` array
2. Show rating dropdown
3. Mark state as dirty
4. Enable save button

When user deselects:
1. Remove from `selectedSkills`
2. Hide rating dropdown
3. Clear any rating
4. Update save button state

## AWS S3 Integration

### S3 Operations

**Read (skills-master.json)**:
```javascript
const params = {
    Bucket: BUCKET_NAME,
    Key: 'skills-master.json'
};

s3.getObject(params, function(err, data) {
    if (err) {
        console.error('Error loading skills:', err);
    } else {
        const skills = JSON.parse(data.Body.toString('utf-8'));
        processSkills(skills);
    }
});
```

**Write (user profile)**:
```javascript
const params = {
    Bucket: BUCKET_NAME,
    Key: `users/${email}.json`,
    Body: JSON.stringify(userProfile),
    ContentType: 'application/json'
};

s3.putObject(params, function(err, data) {
    if (err) {
        console.error('Error saving profile:', err);
    } else {
        console.log('Profile saved successfully');
    }
});
```

**List (user profiles)**:
```javascript
const params = {
    Bucket: BUCKET_NAME,
    Prefix: 'users/'
};

s3.listObjectsV2(params, function(err, data) {
    if (err) {
        console.error('Error listing users:', err);
    } else {
        const users = data.Contents.map(obj => obj.Key);
        displayUsers(users);
    }
});
```

## User Profile Format

### JSON Structure

```json
{
  "email": "user@example.com",
  "created": "2024-10-13T10:30:00Z",
  "updated": "2024-10-13T10:30:00Z",
  "skills": [
    {
      "id": "skill-123",
      "level": 4,
      "title": "AWS Lambda",
      "rating": 3,
      "parent_id": "serverless-456",
      "ancestor_ids": ["cloud-1", "compute-2", "serverless-456"]
    }
  ]
}
```

**Fields**:
- `email`: User identifier (lowercase)
- `created`: First save timestamp (ISO 8601)
- `updated`: Last save timestamp (ISO 8601)
- `skills`: Array of selected skills with ratings
  - `id`: Skill unique identifier
  - `level`: Hierarchy level (1-4)
  - `title`: Skill name
  - `rating`: Proficiency (1=Beginner, 2=Intermediate, 3=Advanced)
  - `parent_id`: Immediate parent skill ID
  - `ancestor_ids`: Full hierarchy path

## Error Handling

### Graceful Degradation

```javascript
try {
    await loadSkillsFromS3();
} catch (error) {
    console.error('Failed to load skills:', error);
    displayError('Unable to load skills. Please refresh the page.');
    // Optionally: Load from fallback source
}
```

### User-Friendly Messages

Map technical errors to user-friendly messages:

```javascript
function handleS3Error(error) {
    const messages = {
        'NoSuchBucket': 'Application not configured correctly',
        'AccessDenied': 'Unable to access data. Please try again',
        'NetworkingError': 'Network error. Check your connection',
        'InvalidAccessKeyId': 'Authentication failed. Please refresh'
    };
    
    const message = messages[error.code] || 'An unexpected error occurred';
    displayError(message);
}
```

### Retry Logic

For transient errors:

```javascript
async function retryOperation(operation, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await operation();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await sleep(Math.pow(2, i) * 1000); // Exponential backoff
        }
    }
}
```

## Performance Optimizations

### Lazy Loading

Only load user profiles when users.html is accessed (not on main page).

### DOM Caching

```javascript
const dom = {
    emailInput: document.getElementById('emailInput'),
    skillsContainer: document.getElementById('skillsContainer'),
    saveButton: document.getElementById('saveButton')
};

// Reuse cached elements instead of querying repeatedly
dom.emailInput.value = user.email;
```

### Event Delegation

Instead of attaching handlers to every checkbox:

```javascript
skillsContainer.addEventListener('change', function(event) {
    if (event.target.type === 'checkbox') {
        handleSkillToggle(event.target);
    } else if (event.target.classList.contains('rating-select')) {
        handleRatingChange(event.target);
    }
});
```

**Benefits**:
- Fewer event listeners
- Works with dynamically added elements
- Better memory usage
