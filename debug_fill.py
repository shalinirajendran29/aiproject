import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path so backend imports work
sys.path.append(os.path.dirname(__file__))

from backend.app.database import SessionLocal
from backend.app.models.document import DBModelDocument
from backend.app.services.automation_engine import PlaywrightAutomationEngine
from backend.app.services.mapping_engine import FieldMappingEngine

def test_fill():
    db = SessionLocal()
    try:
        # Fetch the latest completed document
        doc = db.query(DBModelDocument).filter(DBModelDocument.status == "completed").order_by(DBModelDocument.updated_at.desc()).first()
        if not doc:
            print("No completed documents found.")
            return
            
        print(f"Testing autofill with Document ID: {doc.id}")
        extracted_data = doc.corrected_json or doc.extracted_json
        print(f"Extracted Data: {extracted_data}")
        
        # Support spreadsheet/table row selection (pick index 2 for Kavya to test State/District)
        if "records" in extracted_data and isinstance(extracted_data["records"], list):
            print(f"Spreadsheet detected with {len(extracted_data['records'])} records. Selecting record 2 (Kavya)...")
            extracted_data = extracted_data["records"][2]
            print(f"Selected Record Data: {extracted_data}")
        
        automation_engine = PlaywrightAutomationEngine()
        mapping_engine = FieldMappingEngine()
        
        url = "http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create"
        screenshot_path = os.path.join(os.path.dirname(__file__), "debug_result_screenshot.png")
        
        print("\nExecuting fill_form...")
        result = automation_engine.fill_form(
            url=url,
            extracted_data=extracted_data,
            mapping_engine=mapping_engine,
            db=db,
            screenshot_path=screenshot_path
        )
        
        print("\n=== Result ===")
        print(f"Success: {result['success']}")
        print(f"Filled: {result['filled']}")
        print(f"Errors: {result['errors']}")
        print(f"Mappings: {result['mappings']}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_fill()
