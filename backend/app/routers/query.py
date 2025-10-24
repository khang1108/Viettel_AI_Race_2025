from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.services.embed import embed_texts

router = APIRouter(prefix="/query", tags=["query"])

class QueryIn(BaseModel):
    question: str
    top_k: int | None = None

@router.post("")
def query(q: QueryIn):
    top_k = q.top_k or settings.top_k
    emb = embed_texts([q.question], settings.embed_model_name)[0]
    emb_str = "[" + ",".join(f"{x:.6f}" for x in emb.tolist()) + "]"

    sql = text(f"""
        SELECT content, document_id, ord,
               1 - (embedding <=> {emb_str}::vector) AS score
        FROM chunks
        ORDER BY embedding <-> {emb_str}::vector
        LIMIT :k
    """)
    with engine.begin() as conn:
        rows = conn.exec_driver_sql(sql, {"k": top_k}).mappings().all()

    context = "\n\n".join(r["content"] for r in rows)
    # At this step you can call your LLM. For now return context + scores.
    return {
        "matches": [
            {"content": r["content"], "document_id": str(r["document_id"]), "ord": r["ord"], "score": float(r["score"])}
            for r in rows
        ],
        "context": context
    }
