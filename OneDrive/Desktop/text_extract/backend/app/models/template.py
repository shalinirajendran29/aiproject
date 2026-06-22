from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base

class DBModelWebsiteTemplate(Base):
    __tablename__ = "website_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), nullable=False, unique=True) # e.g. 'portal.company.com'
    field_selectors = Column(JSON, nullable=False)            # e.g. { "email": "input[name='user_mail']", "phone": "#phone" }
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
