from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MappingMemoryBase(BaseModel):
    source_label: str
    target_key: str

class MappingMemoryCreate(MappingMemoryBase):
    pass

class MappingMemoryResponse(MappingMemoryBase):
    id: int
    user_id: str
    frequency_count: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
