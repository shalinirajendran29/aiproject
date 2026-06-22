from pydantic import BaseModel
from typing import Dict
from datetime import datetime

class WebsiteTemplateBase(BaseModel):
    domain: str
    field_selectors: Dict[str, str]

class WebsiteTemplateCreate(WebsiteTemplateBase):
    pass

class WebsiteTemplateResponse(WebsiteTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
