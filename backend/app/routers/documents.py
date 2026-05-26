import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..database import get_db
from ..config import settings
from ..models.document import DBModelDocument
from ..models.mapping import DBModelMappingMemory
from ..schemas.document import DocumentResponse, DocumentReview
from ..services.preprocessor import ImagePreprocessor
from ..services.ocr_engine import OCREngine
from ..services.slm_engine import SLMEngine

router = APIRouter(prefix="/documents", tags=["documents"])

# Shared services instances
ocr_engine = OCREngine()
slm_engine = SLMEngine()

def process_document_task(doc_id: str, db_session_maker):
    """Background task to run OpenCV + OCR + SLM pipeline."""
    db = db_session_maker()
    try:
        # 1. Fetch document from db
        doc = db.query(DBModelDocument).filter(DBModelDocument.id == doc_id).first()
        if not doc:
            return
            
        doc.status = "processing"
        db.commit()
        
        # Paths
        raw_path = doc.storage_path
        preprocessed_filename = f"processed_{os.path.basename(raw_path)}"
        preprocessed_path = os.path.join(settings.UPLOAD_DIR, preprocessed_filename)
        
        # 2. Run OpenCV Preprocessing
        try:
            ImagePreprocessor.preprocess(raw_path, preprocessed_path)
            # Update path to preprocessed for OCR
            ocr_target_path = preprocessed_path
        except Exception as preprocess_err:
            print(f"Preprocessing warning: {preprocess_err}. Proceeding with raw file.")
            ocr_target_path = raw_path
            
        # 3. OCR Extraction
        ocr_res = ocr_engine.extract_text(ocr_target_path)
        doc.ocr_raw_text = ocr_res["raw_text"]
        db.commit()
        
        # 4. SLM Structured Extraction
        extracted_data = slm_engine.extract_fields(ocr_res["raw_text"])
        doc.extracted_json = extracted_data
        
        # Calculate confidence score (simple heuristic here, number of non-null attributes)
        non_null_count = sum(1 for v in extracted_data.values() if v is not None)
        doc.confidence_score = non_null_count / len(extracted_data) if len(extracted_data) > 0 else 0.0
        
        doc.status = "completed"
        db.commit()
        
    except Exception as e:
        print(f"Background task failed for document {doc_id}: {e}")
        doc = db.query(DBModelDocument).filter(DBModelDocument.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save file
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB Record
    db_doc = DBModelDocument(
        filename=file.filename,
        storage_path=file_path,
        mime_type=file.content_type,
        status="pending"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Trigger background pipeline
    from ..database import SessionLocal
    background_tasks.add_task(process_document_task, db_doc.id, SessionLocal)
    
    return db_doc


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DBModelDocument).filter(DBModelDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/{doc_id}/review", response_model=DocumentResponse)
def review_document(
    doc_id: str,
    review_data: DocumentReview,
    db: Session = Depends(get_db)
):
    doc = db.query(DBModelDocument).filter(DBModelDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # 1. Update corrected values
    doc.corrected_json = review_data.corrected_json
    db.commit()
    
    # 2. Learn field-to-key mapping memory
    # We compare original extracted labels with user corrected labels
    # If the user corrects/adds value in a field, we look at the raw OCR text to find the label
    # Here we learn mapping corrections: source label (OCR label) -> normalized target key
    # For instance, if user matches 'user_mail' input to 'email' field, we learn it.
    # In review, we are validating extracted fields. We can check if any field values correspond to
    # specific raw OCR words, and increment mapping frequency count.
    raw_text = doc.ocr_raw_text or ""
    
    for key, val in review_data.corrected_json.items():
        if val and isinstance(val, str):
            # Look up if this value exists in raw OCR text and trace nearby words
            # To simplify, we also allow the client to send mapping correlations, 
            # but we can auto-associate here.
            # Find lines in raw OCR containing the value
            lines = raw_text.split('\n')
            for line in lines:
                if val.lower() in line.lower():
                    # Parse potential label (words preceding the value, e.g., "Mail ID: test@gmail.com")
                    parts = line.split(val)
                    if parts and parts[0].strip():
                        source_label = parts[0].strip().rstrip(":").rstrip("-").strip()
                        if len(source_label) > 1 and len(source_label) < 30:
                            # Save in mapping memory
                            # Upsert mapping memory
                            mapping = db.query(DBModelMappingMemory).filter(
                                DBModelMappingMemory.source_label == source_label,
                                DBModelMappingMemory.target_key == key
                            ).first()
                            
                            if mapping:
                                mapping.frequency_count += 1
                            else:
                                mapping = DBModelMappingMemory(
                                    source_label=source_label,
                                    target_key=key,
                                    frequency_count=1
                                )
                                db.add(mapping)
                            db.commit()
                            break

    db.refresh(doc)
    return doc
