import os
import sys
import numpy as np
import cv2
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.services.preprocessor import ImagePreprocessor
from app.services.ocr_engine import OCREngine
from app.services.slm_engine import SLMEngine
from app.services.mapping_engine import FieldMappingEngine
from app.services.automation_engine import PlaywrightAutomationEngine

def generate_mock_scanned_image(file_path: str):
    """Generates a mock text image using OpenCV with minor skew and noise."""
    # Create white canvas
    img = np.ones((500, 700, 3), dtype=np.uint8) * 255
    
    # Write text mimicking a scanned registration form
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (20, 20, 20)
    
    cv2.putText(img, "PATIENT REGISTRATION RECORD", (80, 50), font, 0.8, (0, 0, 100), 2)
    cv2.putText(img, "---------------------------", (80, 75), font, 0.7, color, 1)
    cv2.putText(img, "Patient Full Name: Kavya Thangavel", (50, 130), font, 0.65, color, 2)
    cv2.putText(img, "Mail ID: kavya@gmail.com", (50, 180), font, 0.65, color, 2)
    cv2.putText(img, "Contact Number: 9876543210", (50, 230), font, 0.65, color, 2)
    cv2.putText(img, "DOB: 15/08/2005", (50, 280), font, 0.65, color, 2)
    cv2.putText(img, "Address: 123 Green Valley, Chennai", (50, 330), font, 0.65, color, 2)
    cv2.putText(img, "Passport ID: K7829102", (50, 380), font, 0.65, color, 2)
    
    # Add noise / skew
    # Rotate by 1.5 degrees to simulate scan skew
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, 1.8, 1.0)
    img_rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    
    # Save the raw distorted file
    cv2.imwrite(file_path, img_rotated)
    print(f"Generated mock scanned image at: {file_path}")

def generate_mock_html_form(file_path: str):
    """Creates a local HTML form mockup with typical web input labels."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Mock Web Portal Form</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f4f6f9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .form-container {
            background: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            width: 400px;
        }
        h2 { margin-bottom: 20px; color: #1e293b; font-size: 1.5rem; text-align: center; }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 6px; font-weight: 600; color: #475569; font-size: 0.9rem; }
        input[type="text"], input[type="email"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 0.95rem;
            transition: border 0.2s;
        }
        input:focus { border-color: #3b82f6; outline: none; }
        .btn-submit {
            width: 100%;
            padding: 12px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Customer Portal Intake</h2>
        <form>
            <div class="form-group">
                <label for="client_name">Client Full Name</label>
                <input type="text" id="client_name" name="client_name" placeholder="Enter full name">
            </div>
            <div class="form-group">
                <label for="user_mail">User E-mail</label>
                <input type="email" id="user_mail" name="user_mail" placeholder="Enter email address">
            </div>
            <div class="form-group">
                <label for="phone_num">Telephone Number</label>
                <input type="text" id="phone_num" name="phone_num" placeholder="Enter contact number">
            </div>
            <div class="form-group">
                <label for="birthdate">Date of Birth</label>
                <input type="text" id="birthdate" name="birthdate" placeholder="DD/MM/YYYY">
            </div>
            <div class="form-group">
                <label for="home_address">Mailing Address</label>
                <input type="text" id="home_address" name="home_address" placeholder="Enter home address">
            </div>
            <div class="form-group">
                <label for="identity_card">ID/Passport Card</label>
                <input type="text" id="identity_card" name="identity_card" placeholder="Enter card identifier">
            </div>
            <button type="button" class="btn-submit" id="submit_btn">Confirm & Submit</button>
        </form>
    </div>
</body>
</html>
"""
    with open(file_path, "w") as f:
        f.write(html_content)
    print(f"Generated mock HTML form at: {file_path}")

def run_pipeline():
    print("=== STARTING INTELLIGENT FORM AUTOMATION PIPELINE ===")
    
    # Directories setup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(base_dir, "pipeline_demo")
    os.makedirs(tmp_dir, exist_ok=True)
    
    raw_img_path = os.path.join(tmp_dir, "raw_form.png")
    processed_img_path = os.path.join(tmp_dir, "processed_form.png")
    mock_form_path = os.path.join(tmp_dir, "portal_form.html")
    screenshot_path = os.path.join(tmp_dir, "filled_form_screenshot.png")
    
    # 1. Generate assets
    generate_mock_scanned_image(raw_img_path)
    generate_mock_html_form(mock_form_path)
    
    # 2. Preprocess using OpenCV
    print("\n--- [Step 2] OpenCV Preprocessing (Deskewing & Thresholding) ---")
    ImagePreprocessor.preprocess(raw_img_path, processed_img_path)
    print(f"Binarized and deskewed form saved to: {processed_img_path}")
    
    # 3. OCR Text Extraction
    print("\n--- [Step 3] EasyOCR Engine text extraction ---")
    ocr = OCREngine()
    ocr_results = ocr.extract_text(processed_img_path)
    print(f"Extracted Raw OCR Text:\n{ocr_results['raw_text']}")
    
    # 4. SLM Information Extraction
    print("\n--- [Step 4] SLM Engine field understanding ---")
    slm = SLMEngine()
    extracted_json = slm.extract_fields(ocr_results["raw_text"])
    print(f"Extracted JSON Fields:\n{json.dumps(extracted_json, indent=2)}")
    
    # 5. Form field crawling on dynamic website
    print("\n--- [Step 5] Playwright Web Element Scraper ---")
    automation = PlaywrightAutomationEngine()
    form_url = f"file:///{mock_form_path.replace(os.sep, '/')}"
    web_fields = automation.inspect_page_forms(form_url)
    print(f"Scraped Form Fields on Target Webpage:")
    for wf in web_fields:
        print(f"  - Label: '{wf['label']}' | Selector: '{wf['selector']}' | Name/ID: '{wf['name'] or wf['id']}'")
        
    # 6. Semantic Field Mapping
    print("\n--- [Step 6] Semantic Field Mapping Engine ---")
    mapper = FieldMappingEngine()
    mapped_selectors = mapper.map_fields(extracted_json, web_fields)
    print("Semantic Matches Found (Key -> Web Selector):")
    print(json.dumps(mapped_selectors, indent=2))
    
    # 7. Playwright Auto-filling
    print("\n--- [Step 7] Playwright Browser Autofill simulation ---")
    # Make sure we run visible so the user could see it (headless=False)
    # We will override setting for the demo script
    automation.headless = True # Set true for non-interactive execution, can be False to watch
    fill_res = automation.fill_form(form_url, mapped_selectors, screenshot_path)
    
    print(f"Autofill Result: {'Success' if fill_res['success'] else 'Failed'}")
    print(f"Filled Fields: {fill_res['filled']}")
    print(f"Errors: {fill_res['errors']}")
    print(f"Completion Verification Screenshot saved to: {screenshot_path}")
    print("\n=== PIPELINE EXECUTION COMPLETED ===")

if __name__ == "__main__":
    run_pipeline()
