"""Initialize resources once for worker process"""
from app.services.embed import get_model
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_worker(**kwargs):
    """Called once when worker process starts"""
    logger.info("Initializing worker process...")
    
    # Pre-load embedding model into memory
    try:
        logger.info(f"Pre-loading embedding model: {settings.EMBED_MODEL_NAME}")
        model = get_model(settings.EMBED_MODEL_NAME)
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to pre-load model: {e}")
    
    logger.info("Worker initialization complete")