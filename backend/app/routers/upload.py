from fastapi import APIRouter, UploadFile, File
from sqlalchemy import text
import os, uuid
from app.core.config import settings
from app.db.session import engine
from app.tasks import ingest_pdf

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("")
def upload_pdf(file: UploadFile = File(...)):
    assert file.content_type in ("application/pdf",), "PDF only"
    os.makedirs(settings.upload_dir, exist_ok=True)
    doc_id = str(uuid.uuid4())
    dest = os.path.join(settings.upload_dir, f"{doc_id}.pdf")
    with open(dest, "wb") as f:
        f.write(file.file.read())
    # record document
    with engine.begin() as conn:
        conn.exec_driver_sql(
            text("""INSERT INTO documents (id, filename, mime_type, bytes) VALUES (:id,:fn,:mt,:sz)"""),
            {"id": doc_id, "fn": file.filename, "mt": file.content_type, "sz": os.path.getsize(dest)},
        )
    task = ingest_pdf.delay(doc_id, dest, file.filename, file.content_type, os.path.getsize(dest))
    return {"document_id": doc_id, "task_id": task.id}
