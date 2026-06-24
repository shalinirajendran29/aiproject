import requests
import json
import re
from typing import Dict, Any, List, Optional
from ..config import settings
class SLMEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.gemini_api_key = settings.GEMINI_API_KEY

    def extract_fields(self, ocr_res: Any) -> Dict[str, Any]:
        """
        Uses Ollama SLM or heuristic tabular alignment to extract structured fields dynamically.
        Falls back to rule-based parser if Ollama is unavailable.
        """

        if isinstance(ocr_res, dict):
            ocr_text = ocr_res.get("raw_text", "")
            words = ocr_res.get("words", [])
        else:
            ocr_text = str(ocr_res)
            words = []
            
        # Try heuristic table extraction first if words are present
        if words:
            table_data = self._extract_table_records(words, ocr_text)
            if table_data and "records" in table_data and len(table_data["records"]) > 0:
                print(f"Table ingestion active: Extracted {len(table_data['records'])} rows.")
                return table_data


        prompt = (
            "You are an AI document parser. Analyze the OCR text below and dynamically identify all labeled fields/attributes and their corresponding values.\n"
            "Identify and extract all keys such as customer/full name, mobile number, address, country, state, district, pin/zip code, PAN number, GSTIN number, company name, website, invoice number, invoice date, total amount, vendor name, item description, gross weight, net weight, purity, making charges, wastage, rate per gram, stone weight, quantity, unit price, discount, hsn/sac code, shipping charges, sku/item code, patient name, doctor name, admission date, discharge date, room number, medicine cost, insurance provider, pnr/booking id, journey date, source location, destination location, seat number, vehicle number, etc.\n"
            "If components of an address (like state, district, or pin_code) are mentioned or embedded, please extract them into separate fields ('state', 'district', 'pin_code') instead of merging them into other unrelated fields.\n"
            "Return the extracted details strictly as a single flat JSON object where the keys are the field names in lowercase snake_case (e.g. 'full_name', 'mobile_number', 'address', 'country', 'state', 'district', 'pin_code', 'pan_no', 'gstin_no', 'invoice_number', 'invoice_date', 'total_amount', 'vendor_name', 'gross_weight', 'net_weight', 'purity', 'making_charges', 'wastage', 'rate_per_gram', 'stone_weight', 'item_description', 'quantity', 'unit_price', 'discount', 'hsn_code', 'shipping_charges', 'sku_code', 'patient_name', 'doctor_name', 'admission_date', 'discharge_date', 'room_number', 'medicine_cost', 'insurance_provider', 'pnr_no', 'journey_date', 'source_location', 'destination_location', 'seat_number', 'vehicle_no') and the values are their extracted strings. "
            "Do not include any explanation or conversational text. Output only the JSON.\n\n"
            f"OCR Text:\n{ocr_text}"

        )
        
        # Check if Google Gemini API key is configured
        if self.gemini_api_key:
            print("Gemini API key detected. Initiating Gemini AI cloud extraction...")
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    result_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(result_text)
                    return self._post_process_data(data, ocr_text)
                else:
                    print(f"Gemini API returned status code {response.status_code}. Falling back to Ollama.")
            except Exception as gemini_err:
                print(f"Gemini API call failed ({gemini_err}). Falling back to Ollama.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",  # Forces Ollama to output valid JSON
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                result_json = response.json().get("response", "{}")
                data = json.loads(result_json)
                return self._post_process_data(data, ocr_text)
        except Exception as e:
            print(f"Ollama SLM inference failed ({e}). Falling back to rule-based heuristics.")
            
        return self._post_process_data(self._regex_fallback_extract(ocr_text), ocr_text)

    def _regex_fallback_extract(self, text: str) -> Dict[str, Any]:
        """
        Dynamically extracts all key-value pairs from the OCR text block.
        Works line-by-line to parse both inline (key: value) and multi-line layouts.
        """
        data = {}
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Lists of words that represent known labels to help with parsing
        # (This helps check if a line is a label or a value)
        known_labels = [
            "name", "full name", "client", "patient", "employee", "customer",
            "email", "mail", "e-mail", "email address",
            "phone", "tel", "telephone", "mobile", "contact", "phone number",
            "date of birth", "dob", "birth date", "birthdate", "date",
            "id", "id number", "license", "passport", "ssn", "identity",
            "address", "addr", "location", "residence", "street",
            "website", "web", "url",
            "linkedin", "social", "social media", "twitter", "facebook",
            "pan", "pan no", "pan card", "gstin", "gstin no", "gst",
            "customer code", "code", "pin code", "pincode", "zip", "zip code",
            "country", "state", "province", "district", "city", "town",
            "invoice number", "invoice no", "bill no", "bill number", "inv no", "receipt no", "inv num",
            "invoice date", "bill date", "inv date", "date issued", "issue date",
            "total amount", "total", "grand total", "amount due", "amount", "total due",
            "vendor name", "vendor", "merchant", "biller", "supplier", "merchant name", "supplier name",
            "gross weight", "gross wt", "gwt", "net weight", "net wt", "nwt", "purity", "karat", "hallmark",
            "making charges", "making charge", "mc", "wastage", "rate", "rate per gram", "stone weight",
            "item description", "description", "particulars", "ornament",
            "qty", "quantity", "quantity ordered", "pieces", "pcs", "nos", "units", "count",
            "unit price", "price per item", "item rate", "unit rate",
            "discount", "discount amount", "promo code", "discount value", "disc", "rebate",
            "hsn", "hsn code", "sac", "sac code",
            "shipping charges", "delivery fee", "shipping", "freight", "postage", "carriage", "courier charges",
            "sku", "item code", "product id", "product code", "article no", "style no", "barcode",
            "patient name", "doctor name", "physician", "surgeon", "consultant", "referred by",
            "admission date", "admitted on", "visit date", "checkin date",
            "discharge date", "discharged on", "checkout date",
            "room number", "room no", "ward no", "bed no", "cabin no",
            "medicine cost", "pharmacy bill", "drug charges", "med cost",
            "insurance provider", "tpa", "insurance co", "payer",
            "pnr", "pnr no", "booking id", "ticket number", "ticket no", "pnr number",
            "journey date", "travel date", "departure date", "departure time", "doj",
            "source", "origin", "from station", "departure from", "boarding point", "from",
            "destination", "to station", "arrival at", "destination city", "to",
            "seat number", "seat no", "berth no", "berth", "seat", "coach no", "cabin",
            "vehicle no", "train no", "train number", "flight no", "flight number", "carrier no", "bus no",
            "declaration", "bank details", "authorized signatory", "signature", "invoice value", "invoice value in words", "net amount", "gross amount", "round off",
            "supplier (bill from)", "buyer (bill to)", "bill to", "bill from", "shipping address", "company's pan"
        ]

        def clean_key(raw_key: str) -> str:
            return self._clean_key_helper(raw_key)

        def is_label(line_text: str) -> bool:
            # A line is a label if it is short (1-4 words) and contains label keywords
            clean = re.sub(r'[^a-zA-Z0-9\s]', '', line_text).strip().lower()
            if not clean:
                return False
            # Exclude table/tax/declaration headers from being treated as labels
            exclude_keywords = {"uom", "cgst", "sgst", "igst", "s no", "s.no", "taxable value", "tax amt", "declaration", "terms", "conditions", "authorized", "signatory", "signature", "bank details", "tcs", "round off"}
            if any(ew in clean for ew in exclude_keywords):
                return False
            # Check length (labels are short)
            words = clean.split()
            if len(words) > 4:
                return False
            # If the clean line is exactly one of our known labels, it's a label
            if clean in known_labels:
                return True
            # Or if it contains specific label phrases (excluding generic value words)
            for w in words:
                if w in known_labels and w not in ["street", "town", "province", "code", "mail", "district", "state", "city", "country"]:
                    return True
            return False

        buttons = {"reset", "save", "submit", "cancel", "clear", "close", "confirm", "create", "update", "delete"}
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Case 0: Space-separated label-value on the same line (e.g. "GSTIN 33BOPP...")
            matched_spaced = False
            if ":" not in line and line.lower().strip() not in known_labels:
                sorted_labels = sorted(known_labels, key=len, reverse=True)
                for label in sorted_labels:
                    line_lower = line.lower()
                    if line_lower.startswith(label + " ") or line_lower.startswith(label + "  "):
                        val_part = line[len(label):].strip()
                        val_part = val_part.lstrip(": -").strip()
                        if val_part:
                            k = clean_key(label)
                            data[k] = val_part
                            matched_spaced = True
                            break
            if matched_spaced:
                i += 1
                continue
            
            # Case 1: Inline extraction using colons (e.g. "Website: www.site.com")
            if ":" in line:
                parts = line.split(":", 1)
                key_part = parts[0].strip()
                val_part = parts[1].strip()
                
                if len(key_part) > 1 and len(key_part) < 30 and is_label(key_part):
                    k = clean_key(key_part)
                    # If value part is not empty, save it
                    if val_part:
                        data[k] = val_part
                        # If it is an address, gather subsequent lines
                        if "address" in k:
                            addr_parts = [val_part]
                            j = i + 1
                            while j < len(lines) and not is_label(lines[j]) and ":" not in lines[j] and lines[j].strip().lower() not in buttons:
                                addr_parts.append(lines[j])
                                j += 1
                            data[k] = ", ".join(addr_parts)
                            i = j - 1
                    # If value part is empty, look at next line
                    elif i + 1 < len(lines) and not is_label(lines[i+1]):
                        data[k] = lines[i+1].strip()
                        i += 1
                    i += 1
                    continue
                    
            # Case 2: Label-Value on separate lines (e.g. "Name \n Olivia Wilson")
            if is_label(line):
                k = clean_key(line)
                # Gather subsequent lines until we hit another label or the end
                val_parts = []
                j = i + 1
                max_lines = 1
                if any(x in k for x in ["address", "description", "particulars", "vendor", "merchant", "supplier", "company"]):
                    max_lines = 4
                while j < len(lines) and len(val_parts) < max_lines and not is_label(lines[j]) and ":" not in lines[j] and lines[j].strip().lower() not in buttons:
                    # Guard: if the value line is a section heading itself, break
                    val_clean = re.sub(r'[^a-zA-Z0-9\s]', '', lines[j]).strip().lower()
                    exclude_keywords = {"uom", "cgst", "sgst", "igst", "s no", "s.no", "taxable value", "tax amt", "declaration", "terms", "conditions", "authorized", "signatory", "signature", "bank details", "tcs", "round off"}
                    if any(ew in val_clean for ew in exclude_keywords):
                        break
                    val_parts.append(lines[j])
                    j += 1
                
                if val_parts:
                    # If we only have one value line, take it
                    if len(val_parts) == 1:
                        data[k] = val_parts[0]
                    else:
                        # For addresses, join with comma, others with space
                        separator = ", " if "address" in k else " "
                        data[k] = separator.join(val_parts)
                    i = j - 1
            i += 1

        return data

    def _post_process_data(self, data: Dict[str, Any], ocr_text: str = "") -> Dict[str, Any]:
        # Standardize keys to lowercase
        processed = {}
        for k, v in data.items():
            if v is not None:
                processed[k.lower()] = v

        # Clean mobile number if present
        if "mobile_number" in processed and processed["mobile_number"]:
            val = str(processed["mobile_number"]).strip()
            # Remove +91 or 91 country code prefix
            if val.startswith("+91"):
                val = val[3:].strip()
            elif val.startswith("91") and len(val) > 10:
                val = val[2:].strip()
            # Keep only digits
            val = "".join(c for c in val if c.isdigit())
            processed["mobile_number"] = val

        # Clean email domain spaces if any (standard correction)
        if "email" in processed and processed["email"] and "@" in processed["email"]:
            parts = processed["email"].split("@")
            if len(parts) == 2:
                domain = parts[1].strip().replace(" ", ".")
                domain = domain.rstrip(".,")
                username = parts[0].strip()
                processed["email"] = f"{username}@{domain}"
                
        # Clean date fields to keep only the date pattern if multiple texts exist
        date_fields = ["invoice_date", "admission_date", "discharge_date", "journey_date", "dob"]
        date_pattern = r'(\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b)'
        for df in date_fields:
            if df in processed and processed[df]:
                val_str = str(processed[df]).strip()
                date_match = re.search(date_pattern, val_str)
                if date_match:
                    processed[df] = date_match.group(1)


        if "dob" not in processed or not processed["dob"]:
            if ocr_text:
                dob_match = re.search(r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})|(?:[A-Za-z]+\s+\d{1,2},\s+\d{4})\b', ocr_text)
                if dob_match:
                    processed["dob"] = dob_match.group(0)

        # ----------------------------------------------------
        # DOMAIN FIELD CORRECTIONS & POST-PROCESSING
        # ----------------------------------------------------
        # 1. GSTIN Clean & Upper
        if "gstin_no" in processed and processed["gstin_no"]:
            processed["gstin_no"] = re.sub(r'[^a-zA-Z0-9]', '', str(processed["gstin_no"])).upper()

        # 2. PAN Number Extraction & Correction
        pan_val = str(processed.get("pan_no", "")).strip()
        is_pan_valid = False
        if pan_val:
            cleaned_pan = re.sub(r'[^a-zA-Z0-9]', '', pan_val).upper()
            corrected_pan = self._clean_and_format_pan(cleaned_pan)
            if corrected_pan:
                processed["pan_no"] = corrected_pan
                is_pan_valid = True

        if not is_pan_valid:
            gstin_val = processed.get("gstin_no", "")
            if gstin_val and len(gstin_val) >= 12:
                pan_candidate = gstin_val[2:12]
                corrected_pan = self._clean_and_format_pan(pan_candidate)
                if corrected_pan:
                    processed["pan_no"] = corrected_pan
                    is_pan_valid = True

        if not is_pan_valid and ocr_text:
            pan_match = re.search(r'\bPAN\b[\s\S]{1,40}\b([A-Z0-9]{10})\b', ocr_text, re.IGNORECASE)
            if pan_match:
                corrected_pan = self._clean_and_format_pan(pan_match.group(1))
                if corrected_pan:
                    processed["pan_no"] = corrected_pan
                    is_pan_valid = True

        # 3. PIN Code Correction
        pin_val = str(processed.get("pin_code", "")).strip()
        pin_digits = "".join(c for c in pin_val if c.isdigit())
        if len(pin_digits) == 6:
            processed["pin_code"] = pin_digits
        else:
            if ocr_text:
                name_query = processed.get("full_name", "") or processed.get("customer_name", "")
                if not name_query:
                    name_query = "Buyer"
                closest_pin = self._find_closest_pincode(ocr_text, name_query)
                if closest_pin:
                    processed["pin_code"] = closest_pin

        # 4. Unit Price, Quantity, Subtotal Mathematical Correction
        if ocr_text:
            qty, price, amt = self._verify_and_extract_line_values(ocr_text)
            if qty and price and amt:
                curr_price = str(processed.get("unit_price", "")).strip()
                if not curr_price or any(c.isalpha() for c in curr_price):
                    processed["unit_price"] = price
                curr_qty = str(processed.get("quantity", "")).strip()
                if not curr_qty or any(c.isalpha() for c in curr_qty):
                    processed["quantity"] = qty

        # 5. Clean Unit Price to be purely numeric
        if "unit_price" in processed and processed["unit_price"]:
            price_str = str(processed["unit_price"]).strip()
            if any(c.isalpha() for c in price_str):
                price_digits = re.findall(r'\b\d+(?:\.\d+)?\b', price_str)
                if price_digits:
                    processed["unit_price"] = price_digits[0]
            else:
                processed["unit_price"] = "".join(c for c in price_str if c.isdigit() or c == '.')

        # 6. Total Amount Correction
        if ocr_text:
            lines = ocr_text.split('\n')
            for line_idx, line in enumerate(lines):
                clean_line = re.sub(r'[^a-zA-Z0-9\s]', '', line).strip().lower()
                if "invoice value" in clean_line and not "words" in clean_line:
                    candidate_lines = lines[line_idx:line_idx+3]
                    found_invoice_value = False
                    for cline in candidate_lines:
                        match = re.search(r'\b\d+\.\d{2}\b', cline)
                        if match:
                            processed["total_amount"] = match.group()
                            found_invoice_value = True
                            break
                    if found_invoice_value:
                        break

        # 7. Clean Vendor Name
        if "vendor_name" in processed and processed["vendor_name"]:
            vendor_str = str(processed["vendor_name"]).strip()
            for term in ["buyers order", "buyer order", "purchase order", "invoice no", "invoice number", "bill to"]:
                pos = vendor_str.lower().find(term)
                if pos != -1:
                    vendor_str = vendor_str[:pos].strip()
            processed["vendor_name"] = vendor_str.rstrip("_,: -")

        # 8. Clean State name from codes (e.g. Code 33 -> TAMILNADU)
        if "state" in processed and processed["state"]:
            state_val = str(processed["state"]).strip()
            if any(c.isdigit() for c in state_val) or "code" in state_val.lower():
                processed["state"] = ""
        
        if not processed.get("state") and ocr_text:
            matches = re.finditer(r'\bState\b', ocr_text, re.IGNORECASE)
            for m in matches:
                sub_text = ocr_text[m.end():m.end()+60]
                words_after = re.findall(r'\b[a-zA-Z]{4,20}\b', sub_text)
                noise = {"code", "gstin", "invoice", "date", "address", "supplier", "buyer", "consignee", "shipping"}
                for w in words_after:
                    if w.lower() not in noise:
                        processed["state"] = w.upper()
                        break
                if processed.get("state"):
                    break
        
        # 9. Clean Bank Details (e.g. "Name of the Bank ICICI" -> "ICICI")
        for key in list(processed.keys()):
            if "bank" in key and processed[key]:
                bank_val = str(processed[key]).strip()
                cleaned_bank = re.sub(
                    r'^(?:name\s+of\s+the\s+bank|name\s+of\s+bank|bank\s+details|bank\s+detail|bank\s+name|bank)\s*[:\-]?\s*',
                    '',
                    bank_val,
                    flags=re.IGNORECASE
                ).strip()
                processed[key] = cleaned_bank
                
        return processed

    def _extract_table_records(self, words: List[Dict[str, Any]], ocr_text: str = "") -> Optional[Dict[str, Any]]:
        """
        Heuristically groups and aligns text blocks horizontally using bounding box center coordinates
        to detect tabular rows and parse spreadsheets of customer records.
        """
        if not words:
            return None

        # 1. Group words into lines vertically based on overlap
        lines_words = []
        current_line = [words[0]]
        for w in words[1:]:
            last_w = current_line[-1]
            last_h = last_w["bbox"][3] - last_w["bbox"][1]
            last_cy = (last_w["bbox"][1] + last_w["bbox"][3]) / 2
            curr_cy = (w["bbox"][1] + w["bbox"][3]) / 2
            
            if abs(curr_cy - last_cy) < 0.6 * last_h:
                current_line.append(w)
            else:
                lines_words.append(current_line)
                current_line = [w]
        lines_words.append(current_line)

        # 2. Helper to group adjacent words in a line into cell text blocks
        distinct_labels = {"name", "phone", "mobile", "contact", "address", "country", "state", "district", "city", "zip", "pincode", "pan", "gstin", "email", "dob"}
        
        def should_avoid_merge(text1: str, text2: str) -> bool:
            clean1 = re.sub(r'[^a-zA-Z0-9\s]', '', text1).strip().lower()
            clean2 = re.sub(r'[^a-zA-Z0-9\s]', '', text2).strip().lower()
            has_label1 = any(dl in clean1 for dl in distinct_labels)
            has_label2 = any(dl in clean2 for dl in distinct_labels)
            if has_label1 and has_label2:
                lbls1 = {dl for dl in distinct_labels if dl in clean1}
                lbls2 = {dl for dl in distinct_labels if dl in clean2}
                if lbls1 != lbls2:
                    return True
            return False

        def get_text_blocks(line_words):
            blocks = []
            if not line_words:
                return blocks
            # Ensure words are sorted left-to-right
            sorted_line = sorted(line_words, key=lambda item: item["bbox"][0])
            current_block = [sorted_line[0]]
            for w in sorted_line[1:]:
                last_w = current_block[-1]
                last_h = last_w["bbox"][3] - last_w["bbox"][1]
                x_gap = w["bbox"][0] - last_w["bbox"][2]
                
                # Check if we should avoid merging them
                current_text = " ".join([item["text"] for item in current_block])
                avoid = should_avoid_merge(current_text, w["text"])
                
                # Merge words that are close horizontally (less than 1.5 * height gap)
                if x_gap < 1.5 * last_h and not avoid:
                    current_block.append(w)
                else:
                    blocks.append({
                        "text": " ".join([item["text"] for item in current_block]),
                        "x_min": current_block[0]["bbox"][0],
                        "x_max": current_block[-1]["bbox"][2]
                    })
                    current_block = [w]
            blocks.append({
                "text": " ".join([item["text"] for item in current_block]),
                "x_min": current_block[0]["bbox"][0],
                "x_max": current_block[-1]["bbox"][2]
            })
            return blocks

        # 3. Search for a header row in the top 4 lines
        known_labels = [
            "name", "full name", "client", "patient", "employee", "customer",
            "email", "mail", "e-mail", "email address",
            "phone", "tel", "telephone", "mobile", "contact", "phone number",
            "date of birth", "dob", "birth date", "birthdate",
            "id", "id number", "license", "passport", "ssn", "identity",
            "address", "addr", "location", "residence", "street",
            "website", "web", "url", "zip", "zipcode", "pincode", "pin", "zip code",
            "pan", "pan no", "pan card", "gstin", "gstin no", "gst",
            "country", "state", "province", "district", "city", "town"
        ]

        header_row_idx = -1
        col_headers = [] # list of {"key": normalized_key, "x_min": x0, "x_max": x1}
        
        for idx, line_words in enumerate(lines_words[:4]):
            blocks = get_text_blocks(line_words)
            matching_blocks_count = 0
            for b in blocks:
                clean_text = b["text"].lower().strip()
                # Check if it matches or contains any known label
                for label in known_labels:
                    if clean_text == label or (len(clean_text) > 2 and clean_text in label) or (len(label) > 2 and label in clean_text):
                        matching_blocks_count += 1
                        break
            
            # If the row has 3 or more column headers matching our keys, we treat it as the Header Row
            if matching_blocks_count >= 3:
                header_row_idx = idx
                for b in blocks:
                    k = self._clean_key_helper(b["text"])
                    col_headers.append({
                        "key": k,
                        "x_min": b["x_min"],
                        "x_max": b["x_max"]
                    })
                break

        # 4. If a header row is found, align data rows under the headers
        records = []
        if header_row_idx != -1:
            for line_words in lines_words[header_row_idx + 1:]:
                if not line_words:
                    continue
                
                # Check if it's a footer or unrelated line (e.g. fewer words than 2, or button labels)
                buttons = {"reset", "save", "submit", "cancel", "clear", "close", "confirm", "create", "update", "delete"}
                line_text_lower = " ".join([w["text"].lower() for w in line_words])
                if len(line_words) < 2 or any(btn == line_text_lower.strip() for btn in buttons):
                    continue

                row_data = {h["key"]: "" for h in col_headers if h["key"]}
                col_words = {h["key"]: [] for h in col_headers if h["key"]}
                
                # Split any word box that contains spaces into separate words with estimated bboxes
                split_line_words = []
                for w in line_words:
                    text = w["text"]
                    bbox = w["bbox"]
                    parts = text.split()
                    if len(parts) <= 1:
                        split_line_words.append(w)
                    else:
                        total_len = len(text)
                        x_min, y_min, x_max, y_max = bbox
                        width = x_max - x_min
                        current_idx = 0
                        for part in parts:
                            start_char_idx = text.find(part, current_idx)
                            if start_char_idx == -1:
                                start_char_idx = current_idx
                            end_char_idx = start_char_idx + len(part)
                            current_idx = end_char_idx
                            
                            p_x_min = x_min + int((start_char_idx / total_len) * width)
                            p_x_max = x_min + int((end_char_idx / total_len) * width)
                            split_line_words.append({
                                "text": part,
                                "bbox": [p_x_min, y_min, p_x_max, y_max]
                            })
                
                for w in split_line_words:
                    w_cx = (w["bbox"][0] + w["bbox"][2]) / 2
                    
                    # Align to the closest column header horizontally using boundary distance
                    best_col = None
                    min_dist = float("inf")
                    for col in col_headers:
                        if not col["key"]:
                            continue
                        if col["x_min"] <= w_cx <= col["x_max"]:
                            dist = 0
                        else:
                            dist = min(abs(w_cx - col["x_min"]), abs(w_cx - col["x_max"]))
                            
                        if dist < min_dist:
                            min_dist = dist
                            best_col = col["key"]
                            
                    if best_col:
                        col_words[best_col].append(w)
                
                # Assemble parsed cell values
                for col_key, words_in_col in col_words.items():
                    if words_in_col:
                        words_in_col.sort(key=lambda item: item["bbox"][0])
                        row_data[col_key] = " ".join([item["text"] for item in words_in_col])
                
                # If there is valid parsed row data, add it to records
                if any(row_data.values()):
                    records.append(self._post_process_data(row_data, ocr_text))
                    
        if records:
            return {"records": records}
        return None

    def _clean_key_helper(self, raw_key: str) -> str:
        # Helper to clean labels into standard snake_case keys (replicates inner clean_key of fallback parser)
        clean = re.sub(r'[^a-zA-Z0-9\s_]', '', raw_key).strip().lower()
        if any(kw in clean for kw in ["code", "id", "identifier", "no", "num", "number"]):
            if "customer" in clean or "client" in clean or "patient" in clean:
                return "customer_code"
            if "pin" in clean or "zip" in clean or "postal" in clean:
                return "pin_code"
            if "pan" in clean:
                return "pan_no"
            if "gst" in clean or "gstin" in clean:
                return "gstin_no"
            if "phone" in clean or "mobile" in clean or "contact" in clean or "tel" in clean:
                return "mobile_number"
            if "invoice" in clean or "inv" in clean or "bill" in clean or "receipt" in clean:
                # Avoid matching Bill To / Bill From / Billing details as invoice_number
                if ("to" in clean or "from" in clean or "ing" in clean or "address" in clean) and "date" not in clean:
                    pass
                else:
                    return "invoice_number"
        if "gst" in clean or "gstin" in clean:
            return "gstin_no"
        if "pan_no" in clean or "pan no" in clean or "pan card" in clean or clean == "pan" or clean.startswith("pan ") or clean.endswith(" pan") or " pan " in clean:
            return "pan_no"
        if "pincode" in clean or "zip" in clean or "postal" in clean or "pin_code" in clean or clean == "pin" or clean.startswith("pin ") or clean.endswith(" pin") or " pin " in clean:
            return "pin_code"
        if "state" in clean or "province" in clean or "region" in clean:
            return "state"
        if "district" in clean or "city" in clean or "town" in clean or "locality" in clean:
            return "district"
        if "country" in clean or clean == "nation" or clean.startswith("nation ") or clean.endswith(" nation") or " nation " in clean:
            return "country"
        if "buyer" in clean or "bill_to" in clean or "bill to" in clean or "consignee" in clean or "receiver" in clean:
            return "full_name"
        if "vendor" in clean or "merchant" in clean or "supplier" in clean or "biller" in clean or "company" in clean or "seller" in clean or "bill_from" in clean or "bill from" in clean:
            return "vendor_name"
        if "source" in clean or "origin" in clean or "boarding" in clean or clean == "from" or clean.startswith("from ") or clean.endswith(" from") or " from " in clean:
            return "source_location"
        if "destination" in clean or "arrival" in clean or clean == "to" or clean.startswith("to ") or clean.endswith(" to") or " to " in clean:
            return "destination_location"
        if "address" in clean or "addr" in clean or "location" in clean or "residence" in clean or "street" in clean:
            return "address"
        if "phone" in clean or "mobile" in clean or "contact" in clean or "tel" in clean or "cell" in clean:
            return "mobile_number"
        if "email" in clean or "mail" in clean:
            return "email"
        if "dob" in clean or "birth" in clean:
            return "dob"
            
        # Put total_amount check BEFORE invoice check to catch "invoice value"
        if "total" in clean or "amount" in clean or "due" in clean or "grand" in clean or "invoice_value" in clean or "invoice value" in clean or "net_amount" in clean or "net amount" in clean or "value" in clean:
            if "medicine" in clean or "pharmacy" in clean or "drug" in clean:
                return "medicine_cost"
            return "total_amount"
            
        if "invoice" in clean or "inv" in clean or "bill" in clean or "receipt" in clean or "date" in clean:
            # Skip Bill To / Bill From / Billing Address/ Billing details (but keep billing date)
            if ("to" in clean or "from" in clean or "ing" in clean or "address" in clean) and "date" not in clean:
                pass
            else:
                if "date" in clean or "day" in clean or "issue" in clean:
                    if "admit" in clean or "admission" in clean or "visit" in clean or "checkin" in clean:
                        return "admission_date"
                    if "discharge" in clean or "checkout" in clean:
                        return "discharge_date"
                    if "travel" in clean or "journey" in clean or "departure" in clean or "doj" in clean:
                        return "journey_date"
                    return "invoice_date"
                if "ticket" in clean or "pnr" in clean or "booking" in clean:
                    return "pnr_no"
                return "invoice_number"
        if "gross" in clean or "gwt" in clean or "grwt" in clean:
            return "gross_weight"
        if "nwt" in clean or "ntwt" in clean or clean == "net" or clean.startswith("net ") or clean.endswith(" net") or " net " in clean:
            return "net_weight"
        if "purity" in clean or "karat" in clean or "hallmark" in clean or clean.endswith("kt") or clean.endswith("ct"):
            return "purity"
        if "making" in clean or clean == "mc" or "making_charges" in clean or "making_charge" in clean:
            return "making_charges"
        if "wastage" in clean or "waste" in clean:
            return "wastage"
        if "rate" in clean or "unit_price" in clean or "price" in clean:
            if "gram" in clean or "gm" in clean or "metal" in clean or "gold" in clean or "silver" in clean:
                return "rate_per_gram"
            return "unit_price"
        if "stone" in clean or "stwt" in clean:
            return "stone_weight"
        if "item" in clean or "description" in clean or "particulars" in clean or "ornament" in clean or "product" in clean or "goods" in clean or "service" in clean:
            return "item_description"
        if "discount" in clean or "disc" in clean or "rebate" in clean or "promo" in clean:
            return "discount"
        if "quantity" in clean or "qty" in clean or "pieces" in clean or "pcs" in clean or "nos" in clean or "units" in clean or clean == "count" or clean.startswith("count ") or clean.endswith(" count") or " count " in clean:
            return "quantity"
        if "hsn" in clean or "sac" in clean:
            return "hsn_code"
        if "shipping" in clean or "delivery" in clean or "freight" in clean or "postage" in clean or "carriage" in clean or "courier" in clean:
            return "shipping_charges"
        if "sku" in clean or "item_code" in clean or "product_code" in clean or "article_no" in clean or "style_no" in clean or "barcode" in clean:
            return "sku_code"
        if "patient" in clean:
            return "patient_name"
        if "doctor" in clean or "physician" in clean or "surgeon" in clean or "referred" in clean:
            return "doctor_name"
        if "admit" in clean or "admission" in clean:
            return "admission_date"
        if "discharge" in clean:
            return "discharge_date"
        if "room" in clean or "ward" in clean or "bed" in clean or "cabin" in clean:
            return "room_number"
        if "medicine" in clean or "pharmacy" in clean or "drug" in clean:
            return "medicine_cost"
        if "insurance" in clean or "tpa" in clean or "payer" in clean:
            return "insurance_provider"
        if "pnr" in clean or "booking_id" in clean or "ticket" in clean:
            return "pnr_no"
        if "journey" in clean or "departure" in clean or "travel" in clean or "doj" in clean:
            return "journey_date"
        if "seat" in clean or "berth" in clean or "coach" in clean:
            return "seat_number"
        if "vehicle" in clean or "train" in clean or "flight" in clean or "bus" in clean:
            return "vehicle_no"
        if "name" in clean or "client" in clean or "patient" in clean or "customer" in clean or "employee" in clean or "owner" in clean:
            return "full_name"
        return re.sub(r'\s+', '_', clean)

    def _clean_and_format_pan(self, raw_val: str) -> str:
        val = re.sub(r'[^a-zA-Z0-9]', '', raw_val).upper()
        if len(val) != 10:
            return ""
        digit_to_letter = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
        letter_to_digit = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8'}
        
        part1 = list(val[0:5])
        for idx, char in enumerate(part1):
            if char.isdigit() and char in digit_to_letter:
                part1[idx] = digit_to_letter[char]
                
        part2 = list(val[5:9])
        for idx, char in enumerate(part2):
            if char.isalpha() and char in letter_to_digit:
                part2[idx] = letter_to_digit[char]
                
        part3 = list(val[9:10])
        for idx, char in enumerate(part3):
            if char.isdigit() and char in digit_to_letter:
                part3[idx] = digit_to_letter[char]
                
        corrected_pan = "".join(part1 + part2 + part3)
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', corrected_pan):
            return corrected_pan
        return val

    def _find_closest_pincode(self, ocr_text: str, name_query: str) -> str:
        if not ocr_text:
            return ""
        pincodes = re.findall(r'\b\d{6}\b', ocr_text)
        if not pincodes:
            return ""
        if len(pincodes) == 1:
            return pincodes[0]
        
        if not name_query or name_query.lower() == "buyer":
            for q in ["buyer (bill to)", "bill to", "ship to", "consignee"]:
                if q in ocr_text.lower():
                    name_query = q
                    break
        
        if name_query:
            pos = ocr_text.lower().find(name_query.lower())
            if pos != -1:
                matches = list(re.finditer(r'\b\d{6}\b', ocr_text))
                closest_pin = ""
                min_dist = float('inf')
                for m in matches:
                    dist = m.start() - pos
                    if dist > 0 and dist < min_dist:
                        min_dist = dist
                        closest_pin = m.group()
                if closest_pin:
                    return closest_pin
        return pincodes[-1]

    def _verify_and_extract_line_values(self, ocr_text: str):
        if not ocr_text:
            return None, None, None
        for line in ocr_text.split('\n'):
            cleaned_line = line.replace(",.", ".").replace(", ", "").replace(" ,", "")
            nums = re.findall(r'\b\d+(?:\.\d+)?\b', cleaned_line)
            clean_nums = []
            for n in nums:
                try:
                    clean_nums.append(float(n))
                except ValueError:
                    pass
            
            for idx in range(len(clean_nums) - 2):
                n1, n2, n3 = clean_nums[idx], clean_nums[idx+1], clean_nums[idx+2]
                if abs(n1 * n2 - n3) < 0.05 * n3 and n1 > 0 and n2 > 0:
                    qty = f"{n1:.2f}" if '.' in str(n1) else str(int(n1))
                    price = f"{n2:.2f}"
                    amt = f"{n3:.2f}"
                    return qty, price, amt
                    
        return None, None, None