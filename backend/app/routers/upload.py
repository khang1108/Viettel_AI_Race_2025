from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Document
import os
import uuid
import aiofiles
from app.core.config import settings
from app.tasks import ingest_pdf

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("")
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a PDF document"""
    
    # Validate file type
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate document ID and path
    doc_id = uuid.uuid4()
    dest = os.path.join(settings.UPLOAD_DIR, f"{doc_id}.pdf")
    
    # Save file asynchronously
    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    file_size = len(content)
    
    # Create document record
    doc = Document(
        id=doc_id,
        filename=file.filename,
        mime_type=file.content_type,
        bytes=file_size
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Queue processing task
    task = ingest_pdf.delay(
        str(doc_id),
        dest,
        file.filename,
        file.content_type,
        file_size
    )
    
    return {
        "document_id": str(doc_id),
        "task_id": task.id,
        "filename": file.filename,
        "size": file_size
    }