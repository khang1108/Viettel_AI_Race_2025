from fastapi import FastAPI
from app.routers import upload, query
from app.routers import task as task_router

app = FastAPI(title="RAG Backend")
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(task_router.router)

@app.get("/health")
def health():
    return {"ok": True}


