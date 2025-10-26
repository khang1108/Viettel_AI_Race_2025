from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, query
from app.routers import task as task_router
from app.core.config import settings
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting RAG Backend...")
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.UPLOAD_DIR}")
    
    # Note: DB tables are created via schema.sql in Docker entrypoint
    # for production. For dev, you can use init_db.py separately
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Backend...")

app = FastAPI(
    title="RAG Backend",
    description="RAG-based Document Processing API with PDF ingestion and semantic search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(task_router.router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": app.version,
        "upload_dir": settings.UPLOAD_DIR,
        "embed_model": settings.EMBED_MODEL_NAME
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "RAG Backend API",
        "docs": "/docs",
        "health": "/health"
    }