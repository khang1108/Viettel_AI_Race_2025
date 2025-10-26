from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None

def get_model(name: str) -> SentenceTransformer:
    """Lazy load and cache the embedding model"""
    global _model
    if _model is None:
        # Set cache directory before loading model
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = settings.SENTENCE_TRANSFORMERS_HOME
        os.environ['TRANSFORMERS_CACHE'] = settings.SENTENCE_TRANSFORMERS_HOME
        os.environ['HF_HOME'] = settings.SENTENCE_TRANSFORMERS_HOME
        
        # Ensure cache directory exists
        os.makedirs(settings.SENTENCE_TRANSFORMERS_HOME, exist_ok=True)
        
        logger.info(f"Loading embedding model: {name}")
        logger.info(f"Model cache location: {settings.SENTENCE_TRANSFORMERS_HOME}")
        _model = SentenceTransformer(name, cache_folder=settings.SENTENCE_TRANSFORMERS_HOME)
    return _model

def embed_texts(texts: List[str], model_name: str) -> np.ndarray:
    """
    Embed a list of texts using sentence-transformers
    Returns normalized embeddings as float32 array
    """
    if not texts:
        return np.array([], dtype="float32")
    
    model = get_model(model_name)
    
    # Encode with normalization for cosine similarity
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 10,
        batch_size=32
    )
    
    return np.asarray(embeddings, dtype="float32")

def embed_query(query: str, model_name: str) -> np.ndarray:
    """Embed a single query text"""
    return embed_texts([query], model_name)[0]