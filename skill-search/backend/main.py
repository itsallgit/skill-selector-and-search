"""
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
import os

from api.routes import router
from services.user_repository import init_repository
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("Starting Skills Search API...")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"AWS Default Profile: {settings.aws_profile}")
    logger.info(f"AWS Default Region: {settings.aws_region}")
    logger.info(f"  → Embedding (Bedrock): {settings.get_embedding_profile()} / {settings.get_embedding_region()}")
    logger.info(f"  → Vector Search: {settings.get_vector_profile()} / {settings.get_vector_region()}")
    logger.info(f"  → Data Ingestion: {settings.get_ingestion_profile()} / {settings.get_ingestion_region()}")
    
    # Initialize user repository
    try:
        logger.info(f"Loading user data from {settings.user_db_path}")
        user_repo = init_repository(settings.user_db_path)
        user_count = len(user_repo.get_all_users())
        logger.info(f"Loaded {user_count} users successfully")
    except Exception as e:
        logger.error(f"Failed to load user data: {str(e)}")
        raise
    
    logger.info("Skills Search API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Skills Search API...")


# Create FastAPI app
app = FastAPI(
    title="Skills Search API",
    description="Semantic search for finding users by skills using natural language queries",
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# Mount static files for data access
# Check if running in Docker (data mounted at /data) or locally (relative path)
if os.path.exists('/data'):
    # Running in Docker with mounted volume
    data_dir = '/data'
else:
    # Running locally - go up from backend/ to skill-search/ to workspace root/ to data/
    backend_dir = os.path.dirname(__file__)
    skill_search_dir = os.path.dirname(backend_dir)
    workspace_root = os.path.dirname(skill_search_dir)
    data_dir = os.path.join(workspace_root, 'data')

if os.path.exists(data_dir):
    app.mount("/data", StaticFiles(directory=data_dir), name="data")
    logger.info(f"Mounted data directory: {data_dir}")
else:
    logger.warning(f"Data directory not found: {data_dir}")


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "service": "Skills Search API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with hot reload for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
