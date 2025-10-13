# Development

> **Note**: For most users, `./skill-search-setup.sh` is recommended. Manual setup is for advanced scenarios or development.

## Backend Development Setup

```bash
cd skill-search/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create and configure .env file
cp .env.example .env
# Edit .env with your AWS configuration (see Configuration section)

# Ingest user data (uses INGESTION_AWS_PROFILE from .env)
python scripts/ingest_users.py

# Override profile if needed
python scripts/ingest_users.py --profile your-profile

# Run backend locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Development Setup

```bash
cd skill-search/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will automatically proxy API requests to `http://localhost:8000`.

## Project Structure

```
skill-search/
├── backend/
│   ├── api/
│   │   ├── models.py          # Pydantic models
│   │   └── routes.py          # REST endpoints
│   ├── services/
│   │   ├── user_repository.py # Data access layer
│   │   ├── vector_search.py   # Vector search service
│   │   └── scoring.py         # Scoring algorithm
│   ├── scripts/
│   │   ├── ingest_users.py    # S3 → user_db.json
│   │   ├── validate_aws.py    # AWS validation
│   │   └── check_vector_index.py # Vector index diagnostics
│   ├── data/
│   │   └── user_db.json       # User database (generated)
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI app
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   └── Dockerfile             # Backend container
├── frontend/
│   ├── public/
│   │   └── index.html         # HTML template
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchPage.js  # Main search interface
│   │   │   ├── SearchBar.js   # Search input
│   │   │   ├── SkillResults.js # Matched skills display
│   │   │   ├── UserResults.js  # User cards
│   │   │   ├── ScoreBuckets.js # Expandable buckets
│   │   │   └── UserDetail.js   # User detail page
│   │   ├── styles/
│   │   │   └── main.css       # Application styles
│   │   ├── App.js             # Main app component
│   │   └── index.js           # React entry point
│   ├── package.json           # Node dependencies
│   └── Dockerfile             # Frontend container
├── scripts/
│   ├── test_api.py            # API test suite
│   └── test_api.sh            # Quick API check
├── docker-compose.yml         # Multi-container setup
├── skill-search-setup.sh      # One-click setup script
└── README-skill-search.md     # This documentation
```
