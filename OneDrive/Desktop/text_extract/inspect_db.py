import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path so backend imports work
sys.path.append(os.path.dirname(__file__))

from backend.app.database import SessionLocal
from backend.app.models.document import DBModelDocument

def inspect():
    db = SessionLocal()
    try:
        docs = db.query(DBModelDocument).order_by(DBModelDocument.updated_at.desc()).all()
        print(f"Total documents: {len(docs)}")
        # print document attributes to see what exists
        if docs:
            print("Document attributes:", [attr for attr in dir(docs[0]) if not attr.startswith('_')])
        for idx, doc in enumerate(docs):
            print(f"\n--- Document {idx}: ID={doc.id}, Status={doc.status} ---")
            print(f"Filename: {getattr(doc, 'filename', 'N/A')}")
            print(f"Extracted JSON: {doc.extracted_json}")
            print(f"Corrected JSON: {doc.corrected_json}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
