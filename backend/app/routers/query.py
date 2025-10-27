from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
import logging
from app.db.session import get_db
from app.core.config import settings
from app.services.embed import embed_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity: float
    document_filename: str | None = None

class QueryResponse(BaseModel):
    query: str
    results: List[SearchResult]
    count: int

@router.get("", response_model=QueryResponse)
async def search_documents(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search documents using semantic similarity
    """
    try:
        # Generate query embedding
        query_vec = embed_query(q, settings.EMBED_MODEL_NAME)
        vec_list = query_vec.tolist() if hasattr(query_vec, "tolist") else list(query_vec)
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec_list) + "]"

        # Use raw SQL with proper parameter binding
        query_sql = text("""
            SELECT 
                c.id::text as chunk_id,
                c.document_id::text as document_id,
                c.content,
                (1 - (c.embedding <=>  CAST(:query_vec AS vector))) as similarity,
                d.filename
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
        """)
        
        # Execute query
        result = await db.execute(query_sql, {"query_vec": vec_str, "top_k": top_k})
        rows = result.fetchall()
        
        # Convert to response model
        results = [
            SearchResult(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                similarity=float(row.similarity),
                document_filename=row.filename
            )
            for row in rows
        ]
        
        return QueryResponse(
            query=q,
            results=results,
            count=len(results)
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")