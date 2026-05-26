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
            "dob": ["date_of_birth", "birthdate", "birthday", "dob", "birth_date"],
            "address": ["street", "location", "residence", "city", "zip", "postal_code", "billing_address", "shipping_address"],
            "id_number": ["ssn", "passport", "license_no", "id_val", "document_id", "identity_number", "id"]
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
        target_clean = target_field_info.lower()
        
        # Guard: prevent "address" from matching "email address"
        if source_key == "address" and ("email" in target_clean or "mail" in target_clean):
            # Only match if it's explicitly about a physical address
            if not any(kw in target_clean for kw in ["home", "mailing", "street", "residence", "postal", "billing", "shipping"]):
                return 0.0
        
        # 1. Check exact or substring containment of primary key
        if source_key in target_clean:
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
        
        # Exclude null values from mapping
        valid_extracted = {k: v for k, v in extracted_data.items() if v is not None}
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
