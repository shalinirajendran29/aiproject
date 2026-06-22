from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base

class DBModelMappingMemory(Base):
    __tablename__ = "mapping_memory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="default")
    source_label = Column(String(255), nullable=False) # e.g., 'Mail ID', 'Contact No.'
    target_key = Column(String(255), nullable=False)   # e.g., 'email', 'phone'
    frequency_count = Column(Integer, default=1)       # incremented when confirmed
    is_verified = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('source_label', 'target_key', name='unique_mapping'),
    )
