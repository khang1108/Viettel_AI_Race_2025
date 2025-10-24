from sqlalchemy import Column, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from app.db.session import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True)
    filename = Column(Text, nullable=False)
    mime_type = Column(Text)
    bytes = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    ord = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    # embedding stored via raw SQL in tasks; SQLAlchemy's Vector type can be added via third-party if desired
