import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..database import get_db
from ..models.document import DBModelDocument
from ..services.automation_engine import PlaywrightAutomationEngine
from ..services.mapping_engine import FieldMappingEngine
from ..config import settings

router = APIRouter(prefix="/automation", tags=["automation"])

# Services
automation_engine = PlaywrightAutomationEngine()
mapping_engine = FieldMappingEngine()

class CrawlRequest(BaseModel):
    url: str

class FillRequest(BaseModel):
    document_id: str
    target_url: str

@router.post("/crawl", response_model=List[Dict[str, Any]])
def crawl_web_fields(request: CrawlRequest):
    """Crawls a target website and lists all visible input fields."""
    try:
        fields = automation_engine.inspect_page_forms(request.url)
        return fields
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web page crawl failed: {str(e)}")


@router.post("/fill")
def fill_web_form(request: FillRequest, db: Session = Depends(get_db)):
    """Maps extracted data from the document and fills the web form using Playwright."""
    # 1. Fetch document
    doc = db.query(DBModelDocument).filter(DBModelDocument.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.status != "completed":
        raise HTTPException(status_code=400, detail=f"Document is in status: {doc.status}. Must be completed.")

    # Get data to fill (use corrected JSON if exists, else extracted JSON)
    extracted_data = doc.corrected_json or doc.extracted_json
    if not extracted_data:
        raise HTTPException(status_code=400, detail="No extracted data found on document to fill.")

    # 2. Crawl website inputs
    try:
        target_fields = automation_engine.inspect_page_forms(request.target_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect target page inputs: {str(e)}")

    if not target_fields:
        raise HTTPException(status_code=400, detail="No input fields found on target website.")

    # 3. Perform Semantic Mapping
    mapped_selectors = mapping_engine.map_fields(extracted_data, target_fields, db)
    if not mapped_selectors:
        return {
            "success": False,
            "message": "No matching fields could be semantically aligned between document and website.",
            "mappings": {},
            "errors": []
        }

    # 4. Fill form and take screenshot
    screenshot_filename = f"screenshot_{doc.id}.png"
    screenshot_path = os.path.join(settings.UPLOAD_DIR, "screenshots", screenshot_filename)
    # Convert absolute path to relative or URL path for frontend
    screenshot_url_path = f"/static/screenshots/{screenshot_filename}"

    try:
        fill_res = automation_engine.fill_form(
            url=request.target_url,
            selector_values=mapped_selectors,
            screenshot_path=screenshot_path
        )
        
        return {
            "success": fill_res["success"],
            "filled_fields": fill_res["filled"],
            "errors": fill_res["errors"],
            "mappings": mapped_selectors,
            "screenshot_url": screenshot_url_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autofill simulation crashed: {str(e)}")
