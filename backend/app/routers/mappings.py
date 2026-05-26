from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.mapping import DBModelMappingMemory
from ..schemas.mapping import MappingMemoryResponse, MappingMemoryCreate

router = APIRouter(prefix="/mappings", tags=["mappings"])

@router.get("/memory", response_model=List[MappingMemoryResponse])
def get_mapping_memory(db: Session = Depends(get_db)):
    """Retrieves all semantic field mappings."""
    return db.query(DBModelMappingMemory).order_by(DBModelMappingMemory.frequency_count.desc()).all()


@router.post("/memory/learn", response_model=MappingMemoryResponse)
def learn_mapping(
    mapping_data: MappingMemoryCreate,
    db: Session = Depends(get_db)
):
    """Manually add or reinforce a field mapping connection."""
    mapping = db.query(DBModelMappingMemory).filter(
        DBModelMappingMemory.source_label == mapping_data.source_label,
        DBModelMappingMemory.target_key == mapping_data.target_key
    ).first()
    
    if mapping:
        mapping.frequency_count += 1
    else:
        mapping = DBModelMappingMemory(
            source_label=mapping_data.source_label,
            target_key=mapping_data.target_key,
            frequency_count=1,
            is_verified=True
        )
        db.add(mapping)
        
    db.commit()
    db.refresh(mapping)
    return mapping
