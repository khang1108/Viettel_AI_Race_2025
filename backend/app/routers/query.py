from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from app.db.session import get_db
from app.core.config import settings
from app.services.embed import embed_query
from app.services.llm import LLMService, LLMResponse

router = APIRouter(prefix="/query", tags=["query"])

# Initialize LLM service
llm_service = LLMService(settings.LLM_MODEL_PATH)

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
    answer: Optional[str] = None
    confidence: Optional[float] = None


@router.post("/query")
async def query_documents(
    query: str,
    contexts: List[str]  # Retrieved from vector search
) -> dict:
    """Query documents using LLM"""
    response = await llm_service.generate(
        query=query,
        context=contexts,
        max_length=settings.LLM_MAX_LENGTH,
        temperature=settings.LLM_TEMPERATURE
    )
    
    return {
        "answer": response.text,
        "confidence": response.confidence
    }

@router.get("", response_model=QueryResponse)
async def search_documents(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    use_llm: bool = Query(False, description="Generate LLM answer"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search documents using semantic similarity
    """
    # Generate query embedding
    query_vec = embed_query(q, settings.EMBED_MODEL_NAME)
    vec_str = "[" + ",".join(f"{x:.6f}" for x in query_vec.tolist()) + "]"
    
    # Search using cosine similarity
    query_sql = text("""
        SELECT 
            c.id as chunk_id,
            c.document_id,
            c.content,
            1 - (c.embedding <=> :query_vec::vector) as similarity,
            d.filename
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        ORDER BY c.embedding <=> :query_vec::vector
        LIMIT :top_k
    """)
    
    result = await db.execute(
        query_sql,
        {"query_vec": vec_str, "top_k": top_k}
    )
    rows = result.fetchall()
    
    results = [
        SearchResult(
            chunk_id=str(row.chunk_id),
            document_id=str(row.document_id),
            content=row.content,
            similarity=float(row.similarity),
            document_filename=row.filename
        )
        for row in rows
    ]
    
    # If LLM is requested, generate answer
    answer = None
    confidence = None
    if use_llm and results:
        contexts = [r.content for r in results]
        llm_response: LLMResponse = await llm_service.generate(
            query=q,
            context=contexts,
            max_length=settings.LLM_MAX_LENGTH,
            temperature=settings.LLM_TEMPERATURE
        )
        answer = llm_response.text
        confidence = llm_response.confidence
    
    return QueryResponse(
        query=q,
        results=results,
        count=len(results)
    )