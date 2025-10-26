import uuid
import logging
from sqlalchemy import create_engine, text
from app.celery_app import celery_app
from app.core.config import settings
from app.services.pdf import extract_pdf_text
from app.services.chunk import split_into_chunks
from app.services.embed import embed_texts

logger = logging.getLogger(__name__)

# Sync engine for Celery workers
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=5
)

@celery_app.task(bind=True, max_retries=3)
def ingest_pdf(self, document_id: str, path: str, filename: str, mime_type: str, size: int):
    """
    Process PDF: extract text, chunk, embed, and store in DB
    """
    try:
        logger.info(f"Processing document {document_id}: {filename}")
        
        # 1. Extract text
        text = extract_pdf_text(path)
        if not text.strip():
            logger.warning(f"No text extracted from {filename}")
            return {"status": "empty", "document_id": document_id}
        
        # 2. Split into chunks
        chunks = split_into_chunks(text)
        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            return {"status": "no_chunks", "document_id": document_id}
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # 3. Generate embeddings
        embeddings = embed_texts(chunks, settings.EMBED_MODEL_NAME)
        
        # 4. Store in database
        with sync_engine.begin() as conn:
            # Bulk insert chunks with embeddings
            for idx, (content, vec) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                vec_str = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"
                
                conn.execute(
                    text("""
                        INSERT INTO chunks (id, document_id, ord, content, token_count, embedding)
                        VALUES (:id, :doc_id, :ord, :content, :tokens, :emb::vector)
                    """),
                    {
                        "id": chunk_id,
                        "doc_id": document_id,
                        "ord": idx,
                        "content": content,
                        "tokens": len(content.split()),
                        "emb": vec_str
                    }
                )
        
        logger.info(f"Successfully processed {filename}: {len(chunks)} chunks")
        return {
            "status": "success",
            "document_id": document_id,
            "chunks": len(chunks),
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)