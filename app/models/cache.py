# app/models/cache.py
import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.core.database import Base

class SemanticCache(Base):
    __tablename__ = "semantic_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_text = Column(Text, nullable=False)
    
    # 384 dimensions is standard for lightweight embedding models (like sentence-transformers)
    embedding = Column(Vector(384), nullable=False) 
    
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)