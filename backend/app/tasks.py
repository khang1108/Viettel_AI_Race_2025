import os, uuid
from sqlalchemy import text
from app.celery_app import celery_app
from app.core.config import settings
from app.db.session import engine
from app.services.pdf import extract_pdf_text
from app.services.chunk import split_into_chunks
from app.services.embed import embed_texts

@celery_app.task
def ingest_pdf(document_id: str, path: str, filename: str, mime_type: str, size: int):
    # 1) Extract text
    text = extract_pdf_text(path)
    if not text.strip():
        return {"status":"empty", "document_id": document_id}

    # 2) Chunk
    chunks = split_into_chunks(text)

    # 3) Embed
    embeddings = embed_texts(chunks, settings.embed_model_name)  # shape (n, dim)

    # 4) Upsert into DB (chunks + vectors)
    dim = settings.embed_dim
    with engine.begin() as conn:
        # ensure pgvector column exists with correct dim
        conn.exec_driver_sql(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({dim});")
        for idx, (content, vec) in enumerate(zip(chunks, embeddings)):
            cid = str(uuid.uuid4())
            conn.exec_driver_sql(
                text("""
                    INSERT INTO chunks (id, document_id, ord, content, token_count, embedding)
                    VALUES (:id, :doc, :ord, :content, :tok, :emb::vector)
                """),
                {
                    "id": cid,
                    "doc": document_id,
                    "ord": idx,
                    "content": content,
                    "tok": len(content.split()),
                    "emb": "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]",
                },
            )
    return {"status": "ok", "chunks": len(chunks), "document_id": document_id}
