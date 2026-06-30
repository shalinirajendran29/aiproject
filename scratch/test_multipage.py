import os
import sys
import json
import pprint
from dotenv import load_dotenv

# Add path so backend is importable
sys.path.append(r"c:\Users\shaba\OneDrive\Desktop\text_extract\aiproject")
load_dotenv(dotenv_path=r"c:\Users\shaba\OneDrive\Desktop\text_extract\backend\.env")

import pypdfium2 as pdfium
from backend.app.database import SessionLocal
from backend.app.models.document import DBModelDocument
from backend.app.routers.documents import process_document_task

def main():
    pdf_path = r"c:\Users\shaba\OneDrive\Desktop\text_extract\aiproject\uploads\GRN Live 6.pdf"
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return
        
    pdf = pdfium.PdfDocument(pdf_path)
    num_pages = len(pdf)
    print(f"GRN Live 6.pdf has {num_pages} pages.")
    
    # 1. Create a dummy document record in SQLite
    db = SessionLocal()
    doc = DBModelDocument(
        filename="GRN Live 6.pdf",
        storage_path=pdf_path,
        mime_type="application/pdf",
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    print(f"Created temporary document record with ID: {doc.id}")
    
    # 2. Run the process_document_task
    print("Running process_document_task...")
    try:
        from backend.app.database import SessionLocal as db_session_maker
        process_document_task(doc.id, db_session_maker)
        
        # 3. Retrieve results from database
        db.refresh(doc)
        print(f"\nTask status: {doc.status}")
        print(f"Confidence score: {doc.confidence_score}")
        print("\nExtracted JSON Keys:")
        pprint.pprint(list(doc.extracted_json.keys()))
        
        print("\nExtracted records count:", len(doc.extracted_json.get("records", [])))
        if len(doc.extracted_json.get("records", [])) > 0:
            print("First record:", doc.extracted_json["records"][0])
            print("Last record:", doc.extracted_json["records"][-1])
            
        print("\nHeader/Footer key values:")
        for k, v in doc.extracted_json.items():
            if k != "records" and k != "_pipeline_metadata":
                print(f"  {k}: {v}")
                
    finally:
        # Cleanup
        db.delete(doc)
        db.commit()
        db.close()

if __name__ == "__main__":
    main()
