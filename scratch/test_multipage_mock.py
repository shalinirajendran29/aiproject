import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Add path so backend is importable
sys.path.append(r"c:\Users\shaba\OneDrive\Desktop\text_extract\aiproject")
load_dotenv(dotenv_path=r"c:\Users\shaba\OneDrive\Desktop\text_extract\backend\.env")

from backend.app.database import SessionLocal
from backend.app.models.document import DBModelDocument

class TestMultiPageStitching(unittest.TestCase):
    @patch("backend.app.routers.documents.ocr_engine")
    @patch("backend.app.routers.documents.slm_engine")
    @patch("pypdfium2.PdfDocument")
    def test_multipage_merging_logic(self, mock_pdf_class, mock_slm, mock_ocr):
        # 1. Setup mock PDF of 2 pages
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 2
        
        mock_page_1 = MagicMock()
        mock_page_2 = MagicMock()
        mock_pdf.__getitem__.side_effect = lambda idx: [mock_page_1, mock_page_2][idx]
        
        mock_pdf_class.return_value = mock_pdf
        
        # 2. Mock OCR extraction responses
        mock_ocr.extract_text.side_effect = [
            {"raw_text": "Page 1 OCR Text content"},
            {"raw_text": "Page 2 OCR Text content"}
        ]
        
        # 3. Mock SLM extraction responses
        # Page 1 contains vendor_name and first record row
        # Page 2 contains total_amount and second record row
        mock_slm.extract_fields.side_effect = [
            {
                "vendor_name": "JEWEL CRAFTS",
                "grn_date": "23/12/2025",
                "records": [{"s_no": 1, "item": "silver A"}]
            },
            {
                "total_amount": 716131.0,
                "total_amount_in_words": "Seven Lakh...",
                "records": [{"s_no": 2, "item": "silver B"}]
            }
        ]
        
        # Create a temp document in database
        db = SessionLocal()
        doc = DBModelDocument(
            filename="dummy_multipage.pdf",
            storage_path="dummy_multipage.pdf",
            mime_type="application/pdf",
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        try:
            from backend.app.routers.documents import process_document_task
            from backend.app.database import SessionLocal as db_session_maker
            process_document_task(doc.id, db_session_maker)
            
            # Refresh doc and verify assertions
            db.refresh(doc)
            self.assertEqual(doc.status, "completed")
            
            extracted = doc.extracted_json
            print("\nMerged Extracted JSON output:\n")
            import pprint
            pprint.pprint(extracted)
            
            # Check headers merged from Page 1
            self.assertEqual(extracted.get("vendor_name"), "JEWEL CRAFTS")
            self.assertEqual(extracted.get("grn_date"), "23/12/2025")
            
            # Check footers merged from Page 2
            self.assertEqual(extracted.get("total_amount"), 716131.0)
            self.assertEqual(extracted.get("total_amount_in_words"), "Seven Lakh...")
            
            # Check stitched records list from Page 1 & Page 2
            records = extracted.get("records")
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["item"], "silver A")
            self.assertEqual(records[1]["item"], "silver B")
            
            print("\nVerification successful! All checks passed.")
            
        finally:
            db.delete(doc)
            db.commit()
            db.close()

if __name__ == "__main__":
    unittest.main()
