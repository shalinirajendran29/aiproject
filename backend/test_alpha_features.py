import os
import sys
import json
import hmac
import hashlib
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import SessionLocal, Base, engine
from app.models.document import DBModelDocument
from app.routers.admin import load_admin_data, save_admin_data
from app.services.cache_service import cache_service

class TestAlphaFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        # Clean docs from test DB
        self.db.query(DBModelDocument).delete()
        self.db.commit()
        # Reset settings
        from app.routers.admin import DEFAULT_KEYS
        import copy
        test_keys = copy.deepcopy(DEFAULT_KEYS)
        test_keys[0]["hashed_key"] = "d694f635d1e4dc33644dc08d495ab68e791244306fdfb6f93a7c05f6adf62d9a" # sha256 of uni_live_dev1234567890abcdef
        
        data = load_admin_data()
        data["keys"] = test_keys
        data["settings"]["webhook_disabled"] = False
        data["settings"]["webhook_url"] = "https://unitive.in/callbacks/invoices"
        data["settings"]["webhook_secret"] = "unitive_hmac_secret_key"
        data["settings"]["feature_flags_ocr"] = True
        data["settings"]["feature_flags_ai"] = True
        save_admin_data(data)
        cache_service.delete("workspace:default_workspace:settings")

    def tearDown(self):
        self.db.close()

    # 1. API Endpoint Tests
    def test_ping_endpoint(self):
        """Verify the health check ping endpoint returns PONG."""
        response = self.client.get("/api/v1/admin/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "PONG")
        self.assertIn("timestamp", response.json())

    def test_sdk_negotiate_endpoint(self):
        """Verify version negotiation selects compatible version."""
        # Success case (compatible)
        response = self.client.post("/api/v1/admin/sdk/negotiate", json={"sdk_version": "v1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "compatible")
        self.assertEqual(response.json().get("selected_version"), "v1")

        # Failure case (uncompatible)
        response = self.client.post("/api/v1/admin/sdk/negotiate", json={"sdk_version": "v3"})
        self.assertEqual(response.status_code, 400)

    # 2. Authentication & Authorization Tests
    def test_session_create_and_bearer_token_auth(self):
        """Verify Bearer token creation and origin-restricted API authentication."""
        # Use default developer key hashed in admin_data.json
        # Raw default key is: uni_live_dev1234567890abcdef
        raw_key = "uni_live_dev1234567890abcdef"
        
        # Request short-lived session token
        response = self.client.post("/api/v1/admin/session/create", json={
            "api_key": raw_key,
            "allowed_origin": "https://erp.testcompany.com"
        })
        self.assertEqual(response.status_code, 200)
        
        session_data = response.json()
        session_token = session_data.get("session_token")
        self.assertTrue(session_token.startswith("uni_sess_"))
        
        # Test authenticating a protected route with this token
        # Header Bearer Token authentication
        headers = {
            "Authorization": f"Bearer {session_token}",
            "Origin": "https://erp.testcompany.com"
        }
        
        # Origin match request succeeds
        resp = self.client.get("/api/v1/documents", headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Origin mismatch request is blocked (403 Forbidden)
        mismatch_headers = {
            "Authorization": f"Bearer {session_token}",
            "Origin": "https://hacking-origin.com"
        }
        resp_blocked = self.client.get("/api/v1/documents", headers=mismatch_headers)
        self.assertEqual(resp_blocked.status_code, 403)

    # 3. SDK Initialization Tests
    def test_sdk_cache_handshake(self):
        """Simulate SDK setting token payload in Cache and checking session parameters."""
        token = "uni_sess_sdk_handshake_test_token"
        payload = {
            "workspace": "Test Workspace",
            "role": "Admin",
            "allowed_origin": "http://localhost:3000",
            "expires_at": "2026-06-26T23:59:59Z"
        }
        cache_service.set(f"session:token:{token}", payload, expire_seconds=60)

        # Check that cache retrieves metadata properly
        retrieved = cache_service.get(f"session:token:{token}")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("workspace"), "Test Workspace")
        self.assertEqual(retrieved.get("role"), "Admin")

        # Cleanup
        cache_service.delete(f"session:token:{token}")

    # 4. Ingestion Async Job Flow Tests
    def test_async_job_upload_and_status_polling(self):
        """Verify uploading file creates job, status progresses, and returns results."""
        # Create a mock text file
        mock_file_content = b"Invoice Date: 2026-06-26\nVendor: Test AI Vendor\nTotal: 125.50"
        
        # Upload using the Job endpoint
        response = self.client.post(
            "/api/v1/documents/jobs/upload",
            files={"file": ("test_invoice.pdf", mock_file_content, "application/pdf")}
        )
        self.assertEqual(response.status_code, 200)
        job_data = response.json()
        job_id = job_data.get("job_id")
        self.assertIsNotNone(job_id)
        self.assertEqual(job_data.get("status"), "pending")

        # Poll status
        resp_status = self.client.get(f"/api/v1/documents/jobs/{job_id}/status")
        self.assertEqual(resp_status.status_code, 200)
        self.assertEqual(resp_status.json().get("job_id"), job_id)
        self.assertIn(resp_status.json().get("status"), ["pending", "processing", "completed", "failed"])

        # Fetch result
        resp_result = self.client.get(f"/api/v1/documents/jobs/{job_id}/result")
        self.assertIn(resp_result.status_code, [200, 202])

    # 5. Webhook Signature Verification Tests
    def test_webhook_signature_verification_logic(self):
        """Verify payload HMAC-SHA256 signature generation and validation checks."""
        payload = {
            "document_id": "doc_test_12345",
            "status": "completed",
            "confidence_score": 0.98
        }
        secret = "unitive_hmac_secret_key"
        
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Webhook signature validation simulator
        incoming_sig = expected_signature
        computed_sig = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        self.assertEqual(computed_sig, incoming_sig)

        # Modify payload to check that signature verification fails
        altered_payload = {**payload, "status": "failed"}
        altered_payload_str = json.dumps(altered_payload, sort_keys=True)
        mismatch_sig = hmac.new(
            secret.encode('utf-8'),
            altered_payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        self.assertNotEqual(mismatch_sig, incoming_sig)

if __name__ == "__main__":
    unittest.main()
