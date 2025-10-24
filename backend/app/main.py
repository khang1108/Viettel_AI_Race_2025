from fastapi import FastAPI
from app.routers import upload, query

app = FastAPI(title="RAG Backend")
app.include_router(upload.router)
app.include_router(query.router)

@app.get("/health")
def health():
    return {"ok": True}
