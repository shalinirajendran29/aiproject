import numpy as np
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models.mapping import DBModelMappingMemory
from ..config import settings

class FieldMappingEngine:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._model = None
        
        # Hardcoded synonym fallback for fast zero-shot execution
        self.synonyms = {
            "full_name": ["name", "fullname", "username", "first_name", "last_name", "first", "last", "client_name", "owner"],
            "email": ["mail", "email_address", "user_mail", "contact_email", "eposta", "login_email"],
            "phone": ["tel", "telephone", "mobile", "phone_number", "contact_no", "cell", "fax"],
            "mobile_number": ["tel", "telephone", "mobile", "phone_number", "mobile_number", "contact_no", "cell", "fax"],
            "dob": ["date_of_birth", "birthdate", "birthday", "dob", "birth_date"],
            "address": ["street", "location", "residence", "city", "zip", "postal_code", "billing_address", "shipping_address"],
            "id_number": ["ssn", "passport", "license_no", "id_val", "document_id", "identity_number", "id"],
            "pan_no": ["pan", "pan_no", "pan_number", "permanent_account_number"],
            "gstin_no": ["gst", "gstin", "gstin_no", "gstin_number", "tax_number"],
            "country": ["country", "nation", "country_name"],
            "state": ["state", "province", "region", "state_name"],
            "district": ["district", "city", "town", "locality", "suburb"],
            "pin_code": ["pin_code", "pincode", "zip", "zipcode", "postal", "postal_code", "zip_code"],
            "invoice_number": ["invoice_number", "invoice_no", "bill_no", "bill_number", "inv_no", "receipt_no", "inv_num", "invoice number", "invoice no", "bill no", "bill number", "receipt number"],
            "invoice_date": ["invoice_date", "bill_date", "inv_date", "date_issued", "issue_date", "invoice date", "bill date", "date of issue"],
            "total_amount": ["total_amount", "total", "grand_total", "amount_due", "amount", "total_due", "total amount", "grand total", "net amount", "invoice amount", "sum due"],
            "vendor_name": ["vendor_name", "vendor", "merchant", "biller", "supplier", "merchant_name", "vendor name", "company name", "company", "supplier name"],
            "gross_weight": ["gross_weight", "gross weight", "gr_wt", "gwt", "gross wt", "grossweight"],
            "net_weight": ["net_weight", "net weight", "nt_wt", "nwt", "net wt", "netweight"],
            "purity": ["purity", "karat", "carat", "kt", "ct", "hallmark", "gold_purity", "purity_percent"],
            "making_charges": ["making_charges", "making charges", "making charge", "making chg", "mc", "making_charge"],
            "wastage": ["wastage", "wastage_percent", "wastage weight", "wastage wt", "wastage %", "wastage_wt"],
            "rate_per_gram": ["rate", "rate_per_gram", "gold_rate", "rate/gm", "metal_rate", "gold rate", "rate per gram"],
            "stone_weight": ["stone_weight", "stone weight", "st_wt", "stone wt", "stone_wt"],
            "item_description": ["item", "description", "item_description", "jewel_type", "ornament", "particulars", "item description", "product_name", "product", "goods", "service", "particulars", "description of goods"],
            "quantity": ["qty", "quantity", "quantity_ordered", "pieces", "pcs", "nos", "units", "count"],
            "unit_price": ["unit_price", "rate", "price", "price_per_item", "item_rate", "unit_rate", "rate_per_piece"],
            "discount": ["discount", "discount_amount", "promo_code", "discount_value", "disc", "rebate", "less"],
            "hsn_code": ["hsn", "hsn_code", "sac", "sac_code", "hsn_sac_code", "tax_classification"],
            "shipping_charges": ["shipping_charges", "delivery_fee", "shipping", "freight", "postage", "carriage", "courier_charges"],
            "sku_code": ["sku", "item_code", "product_id", "product_code", "article_no", "style_no", "barcode"],
            "patient_name": ["patient_name", "patient", "patient_id", "sick_person", "admitted_patient", "patient name"],
            "doctor_name": ["doctor_name", "doctor", "physician", "surgeon", "consultant", "referred_by", "doctor name"],
            "admission_date": ["admission_date", "admitted_on", "visit_date", "checkin_date", "admission_day", "admit_date", "admission date"],
            "discharge_date": ["discharge_date", "discharged_on", "checkout_date", "discharge_day", "discharge date"],
            "room_number": ["room_number", "room_no", "ward_no", "bed_no", "room_id", "cabin_no", "room number"],
            "medicine_cost": ["medicine_cost", "pharmacy_bill", "drug_charges", "medicine_amount", "med_cost", "medicine cost"],
            "insurance_provider": ["insurance_provider", "tpa", "insurance_co", "payer", "insurance_name", "tpa_name", "insurance provider"],
            "pnr_no": ["pnr", "pnr_no", "booking_id", "ticket_number", "ticket_no", "pnr_number", "booking_reference", "reference_no", "ticket no", "pnr number"],
            "journey_date": ["journey_date", "travel_date", "departure_date", "departure_time", "event_date", "date_of_journey", "doj", "journey date"],
            "source_location": ["source", "origin", "from_station", "departure_from", "boarding_point", "source_city", "from", "source location"],
            "destination_location": ["destination", "to_station", "arrival_at", "destination_city", "to", "destination location"],
            "seat_number": ["seat_number", "seat_no", "berth_no", "berth", "seat", "coach_no", "cabin", "seat number"],
            "vehicle_no": ["vehicle_no", "train_no", "train_number", "flight_no", "flight_number", "carrier_no", "bus_no", "vehicle no", "train no", "flight no"]
        }

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"Failed to load SentenceTransformer ({e}). Falling back to string matchers.")
        return self._model

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _get_string_match_score(self, source_key: str, target_field_info: str) -> float:
        """Fallback lexical overlap scorer if SentenceTransformers is offline."""
        source_clean = source_key.lower().replace('_', ' ')
        target_clean = target_field_info.lower()
        
        # Guard: prevent "address" from matching "email address"
        if source_clean == "address" and ("email" in target_clean or "mail" in target_clean):
            # Only match if it's explicitly about a physical address
            if not any(kw in target_clean for kw in ["home", "mailing", "street", "residence", "postal", "billing", "shipping"]):
                return 0.0
        
        # 1. Check exact or substring containment of primary key
        if source_clean in target_clean or source_key in target_clean:
            return 0.8
            
        # 2. Check synonyms
        for syn in self.synonyms.get(source_key, []):
            if syn in target_clean:
                return 0.7
                
        return 0.0

    def map_fields(
        self,
        extracted_data: Dict[str, Any],
        form_fields: List[Dict[str, Any]],
        db: Optional[Session] = None
    ) -> Dict[str, str]:
        """
        Maps extracted JSON keys to website form field selectors.
        
        form_fields structure:
        [
            {
                "id": "user_mail",
                "name": "user_mail",
                "type": "email",
                "placeholder": "Enter Mail",
                "label": "Email Address",
                "selector": "input[name='user_mail']"
            },
            ...
        ]
        
        Returns:
            {
                "selector_string": "value_to_fill"
            }
        """
        mappings = {}
        
        # Exclude null/empty values from mapping and system-generated code keys
        keys_to_exclude = {"code", "customer_code", "customer_id", "id"}
        valid_extracted = {k: v for k, v in extracted_data.items() if v is not None and str(v).strip() != "" and k.lower() not in keys_to_exclude}
        
        # Intelligently parse sub-fields from address if they don't exist in extracted_data
        address = valid_extracted.get("address")
        if address and isinstance(address, str):
            # Parse PIN code: 6-digit or 4-digit zip/pin code
            pin_match = re.search(r'\b\d{4,6}\b', address)
            if pin_match and "pin_code" not in valid_extracted and "zip" not in valid_extracted:
                valid_extracted["pin_code"] = pin_match.group(0)
                
            # Parse Country
            countries = ["India", "Australia", "United States", "USA", "United Kingdom", "UK", "Canada"]
            for c in countries:
                if re.search(r'\b' + re.escape(c) + r'\b', address, re.IGNORECASE):
                    if "country" not in valid_extracted:
                        valid_extracted["country"] = c
                    break
                    
            # Parse State
            states = ["VIC", "Victoria", "NSW", "New South Wales", "QLD", "Queensland", "Tamil Nadu", "Tamilnadu", "TN", "Kerala", "KL", "Karnataka", "KA", "Delhi", "Maharashtra", "MH"]
            for s in states:
                if re.search(r'\b' + re.escape(s) + r'\b', address, re.IGNORECASE):
                    if "state" not in valid_extracted:
                        valid_extracted["state"] = s
                    break

        if not valid_extracted:
            return mappings

        # Prepare semantic representations of target form fields
        field_descriptions = []
        for field in form_fields:
            # Create a string detailing all semantic information of the web field
            attributes = [
                field.get("name", ""),
                field.get("id", ""),
                field.get("placeholder", ""),
                field.get("label", ""),
                field.get("type", "")
            ]
            desc = " ".join([attr.lower() for attr in attributes if attr])
            field_descriptions.append((field["selector"], desc))

        # Check DB mapping memory first for fast resolution
        db_memory = {}
        if db:
            try:
                db_records = db.query(DBModelMappingMemory).filter(DBModelMappingMemory.is_verified == True).all()
                for rec in db_records:
                    db_memory[rec.source_label.lower()] = rec.target_key
            except Exception as e:
                print(f"Error reading mapping memory from DB: {e}")

        # Vectorize if Model is available
        model_active = self.model is not None
        if model_active:
            try:
                extracted_keys = list(valid_extracted.keys())
                key_embeddings = self.model.encode(extracted_keys)
                desc_embeddings = self.model.encode([desc for _, desc in field_descriptions])
            except Exception as e:
                print(f"Embedding encoding failed ({e}). Reverting to synonym rules.")
                model_active = False

        assigned_selectors = set()
        assigned_source_keys = set()

        # Step 1: Query historical DB memory first
        for source_key, value in valid_extracted.items():
            matched_from_db = False
            for selector, desc in field_descriptions:
                # If historical memory contains this desc mapped to source_key
                for word in re.split(r'[^a-zA-Z0-9_]', desc):
                    if word and db_memory.get(word) == source_key:
                        mappings[selector] = value
                        assigned_selectors.add(selector)
                        assigned_source_keys.add(source_key)
                        matched_from_db = True
                        break
                if matched_from_db:
                    break

        # Step 2: Compute hybrid semantic/lexical scores for all remaining pairs
        scored_pairs = []
        for source_key, value in valid_extracted.items():
            if source_key in assigned_source_keys:
                continue
            for idx, (selector, desc) in enumerate(field_descriptions):
                if selector in assigned_selectors:
                    continue
                    
                semantic_score = 0.0
                if model_active:
                    # Get index of current source_key
                    key_idx = list(valid_extracted.keys()).index(source_key)
                    semantic_score = self.cosine_similarity(key_embeddings[key_idx], desc_embeddings[idx])
                
                lexical_score = self._get_string_match_score(source_key, desc)
                
                # Use the highest matching score
                score = max(semantic_score, lexical_score)
                
                # Boost direct synonym matches to guarantee they cross the threshold
                if lexical_score >= 0.7:
                    score = max(score, 0.8)
                    
                scored_pairs.append({
                    "source_key": source_key,
                    "value": value,
                    "selector": selector,
                    "score": score
                })
                
        # Sort pairs by score descending
        scored_pairs.sort(key=lambda x: x["score"], reverse=True)
        
        # Step 3: Greedy assignment of remaining pairs
        threshold = 0.38 if model_active else 0.5
        for pair in scored_pairs:
            source_key = pair["source_key"]
            selector = pair["selector"]
            score = pair["score"]
            value = pair["value"]
            
            if score < threshold:
                continue
                
            if selector not in assigned_selectors and source_key not in assigned_source_keys:
                mappings[selector] = value
                assigned_selectors.add(selector)
                assigned_source_keys.add(source_key)
                
        return mappings
