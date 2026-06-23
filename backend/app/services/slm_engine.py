import requests
import json
import re
from typing import Dict, Any
from ..config import settings
class SLMEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def extract_fields(self, ocr_text: str) -> Dict[str, Any]:
        """
        Uses Ollama SLM to extract structured fields.
        Falls back to rule-based parser if Ollama is unavailable.
        """
        
        prompt = (
            "You are an AI document parser. Extract key fields from the text below.\n"
            "Identify the following attributes if present:\n"
            "- full_name (person's name)\n"
            "- email (email address)\n"
            "- phone (phone number)\n"
            "- dob (date of birth)\n"
            "- address (mailing/home address)\n"
            "- id_number (passport, license, or standard ID number)\n\n"
            "Format the output strictly as a single JSON object with these keys. "
            "Use null for values not found in the text. Do not add any text before or after the JSON.\n\n"
            f"OCR Text:\n{ocr_text}"

        )
        
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
                timeout=15
            )
            if response.status_code == 200:
                result_json = response.json().get("response", "{}")
                return json.loads(result_json)
        except Exception as e:
            print(f"Ollama SLM inference failed ({e}). Falling back to rule-based heuristics.")
            
        return self._regex_fallback_extract(ocr_text)

    def _regex_fallback_extract(self, text: str) -> Dict[str, Any]:
        """Heuristic rule-based fallback extraction if local SLM is offline."""
        data = {
            "full_name": None,
            "email": None,
            "phone": None,
            "dob": None,
            "address": None,
            "id_number": None
        }
        
        # Split text into clean lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Helper to check if a line looks like a known label
        def is_label(line_text: str) -> bool:
            clean = line_text.lower().rstrip(':').rstrip('-').strip()
            labels = [
                "name", "full name", "patient", "employee",
                "email", "mail", "email address",
                "phone", "tel", "telephone", "mobile", "contact",
                "date of birth", "dob", "birth date", "birthdate",
                "id", "id number", "license", "passport", "ssn",
                "address", "addr", "location", "website", "social media", "social"
            ]
            return clean in labels

        # Let's search line by line
        for i, line in enumerate(lines):
            # Check for name
            if re.match(r'^(?:Name|Full\s*Name|Patient|Employee)$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["name", "full name"]:
                # Check inline first
                inline_match = re.search(r'(?:Name|Full\s*Name):\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["full_name"] = inline_match.group(1).strip()
                elif i + 1 < len(lines) and not is_label(lines[i+1]):
                    data["full_name"] = lines[i+1].strip()

            # Check for DOB
            elif re.match(r'^(?:Date\s*Of\s*Birth|DOB|Birth\s*Date)$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["date of birth", "dob", "birth date"]:
                inline_match = re.search(r'(?:Date\s*Of\s*Birth|DOB|Birth\s*Date):\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["dob"] = inline_match.group(1).strip()
                elif i + 1 < len(lines) and not is_label(lines[i+1]):
                    data["dob"] = lines[i+1].strip()

            # Check for ID Number
            elif re.match(r'^(?:ID|License|Passport|SSN)(?:\s*Number|\s*No\.?)?$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["id", "id number", "license", "passport", "ssn"]:
                inline_match = re.search(r'(?:ID|License|Passport|SSN)(?:\s*Number|\s*No\.?)?:\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["id_number"] = inline_match.group(1).strip()
                elif i + 1 < len(lines) and not is_label(lines[i+1]):
                    data["id_number"] = lines[i+1].strip()

            # Check for Phone
            elif re.match(r'^(?:Phone|Tel|Telephone|Mobile)$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["phone", "tel", "telephone", "mobile"]:
                inline_match = re.search(r'(?:Phone|Tel|Telephone|Mobile):\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["phone"] = inline_match.group(1).strip()
                elif i + 1 < len(lines) and not is_label(lines[i+1]):
                    data["phone"] = lines[i+1].strip()

            # Check for Email
            elif re.match(r'^(?:Email|Mail|Email\s*Address)$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["email", "mail", "email address"]:
                inline_match = re.search(r'(?:Email|Mail|Email\s*Address):\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["email"] = inline_match.group(1).strip()
                elif i + 1 < len(lines) and not is_label(lines[i+1]):
                    data["email"] = lines[i+1].strip()

            # Check for Address
            elif re.match(r'^(?:Address|Addr|Location)$', line, re.IGNORECASE) or line.lower().rstrip(':').strip() in ["address", "addr", "location"]:
                inline_match = re.search(r'(?:Address|Addr|Location):\s*(.+)', line, re.IGNORECASE)
                if inline_match and len(inline_match.group(1).strip()) > 1:
                    data["address"] = inline_match.group(1).strip()
                elif i + 1 < len(lines):
                    # Gather subsequent lines until we hit a label
                    addr_parts = []
                    j = i + 1
                    while j < len(lines) and not is_label(lines[j]):
                        addr_parts.append(lines[j])
                        j += 1
                    if addr_parts:
                        data["address"] = ", ".join(addr_parts)

        # Global regex fallbacks if any fields are still None
        if not data["email"]:
            # Match standard email or relaxed email (with spaces/missing dots due to OCR)
            email_match = re.search(r'[\w\.-]+@[\w\.-]+(?:\s+|\.)\w+', text)
            if email_match:
                # Clean up email if it contains spaces
                cleaned_email = email_match.group(0).replace(" ", ".")
                data["email"] = cleaned_email
            else:
                # Fallback to any line containing '@'
                for line in lines:
                    if "@" in line and not is_label(line):
                        data["email"] = line.strip().replace(" ", ".")
                        break

        # Clean email domain spaces if any
        if data["email"] and "@" in data["email"]:
            parts = data["email"].split("@")
            if len(parts) == 2:
                domain = parts[1].strip().replace(" ", ".")
                domain = domain.rstrip(".,")
                username = parts[0].strip()
                data["email"] = f"{username}@{domain}"
                        
        if not data["phone"]:
            phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if phone_match:
                data["phone"] = phone_match.group(0)

        if not data["dob"]:
            dob_match = re.search(r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})|(?:[A-Za-z]+\s+\d{1,2},\s+\d{4})\b', text)
            if dob_match:
                data["dob"] = dob_match.group(0)
        return data