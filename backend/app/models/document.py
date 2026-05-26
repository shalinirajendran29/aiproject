import uuid
from sqlalchemy import Column, String, Text, JSON, Numeric, DateTime
from sqlalchemy.sql import func
from ..database import Base

class DBModelDocument(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    ocr_raw_text = Column(Text, nullable=True)
    extracted_json = Column(JSON, nullable=True)
    corrected_json = Column(JSON, nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
