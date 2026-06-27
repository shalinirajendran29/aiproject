import os
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, Any, List
from datetime import datetime
from ..config import settings
from .cache_service import cache_service

HISTORY_FILE = os.path.join(settings.UPLOAD_DIR, "webhook_history.json")

def load_webhook_history() -> Dict[str, Any]:
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "dlq": []}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"history": [], "dlq": []}

def save_webhook_history(data: Dict[str, Any]):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save webhook history: {e}")

def get_consecutive_failures() -> int:
    val = cache_service.get("webhook:consecutive_failures")
    return int(val) if val is not None else 0

def increment_consecutive_failures() -> int:
    val = get_consecutive_failures() + 1
    cache_service.set("webhook:consecutive_failures", val, expire_seconds=86400)
    return val

def reset_consecutive_failures():
    cache_service.set("webhook:consecutive_failures", 0, expire_seconds=86400)

def dispatch_webhook_sync(webhook_url: str, payload: Dict[str, Any], secret: str, doc_id: str):
    """
    Synchronous webhook runner with exponential backoff and retries.
    """
    from ..routers.admin import append_admin_log, load_admin_data, save_admin_data

    # Check if disabled
    admin_data = load_admin_data()
    if admin_data.get("settings", {}).get("webhook_disabled", False):
        append_admin_log("webhook", "WARNING", f"Webhook delivery bypassed for Doc {doc_id} because webhook dispatcher is disabled due to repeated failures.")
        return

    # Compute HMAC Signature
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode('utf-8') if secret else b"default_secret",
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature,
        "X-Correlation-ID": payload.get("correlation_id", "unknown")
    }

    max_retries = 5
    backoff_factor = 1.5
    success = False
    attempts = []

    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        status_code = None
        error_msg = None
        response_body = None

        try:
            # Short timeout to avoid blocking threads
            res = requests.post(webhook_url, json=payload, headers=headers, timeout=5.0)
            status_code = res.status_code
            response_body = res.text[:200] # limit size
            if 200 <= status_code < 300:
                success = True
        except requests.exceptions.RequestException as e:
            error_msg = str(e)

        duration = round(time.time() - start_time, 3)
        attempt_record = {
            "attempt": attempt,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status_code": status_code,
            "duration_sec": duration,
            "error": error_msg,
            "response": response_body
        }
        attempts.append(attempt_record)

        if success:
            break
        
        # Backoff wait
        if attempt < max_retries:
            sleep_time = backoff_factor * (2 ** (attempt - 1))
            time.sleep(sleep_time)

    # Load and update history
    history_data = load_webhook_history()
    log_item = {
        "document_id": doc_id,
        "webhook_url": webhook_url,
        "success": success,
        "attempts": attempts,
        "payload_snippet": payload_str[:150]
    }
    history_data["history"].insert(0, log_item)
    history_data["history"] = history_data["history"][:200] # Cap size

    if success:
        reset_consecutive_failures()
        append_admin_log("webhook", "INFO", f"Webhook delivery succeeded for Doc {doc_id} on attempt {len(attempts)}.")
    else:
        # Failure logic
        consecutive_failures = increment_consecutive_failures()
        history_data["dlq"].append(log_item)
        append_admin_log("webhook", "ERROR", f"Webhook delivery failed for Doc {doc_id} after {max_retries} attempts. Appended to Dead-Letter Queue (DLQ). Consecutive failures: {consecutive_failures}/5")

        if consecutive_failures >= 5:
            # Disable webhook auto-safety switch
            admin_data = load_admin_data()
            admin_data["settings"]["webhook_disabled"] = True
            save_admin_data(admin_data)
            append_admin_log("webhook", "CRITICAL", "Webhooks have been DISABLED automatically due to 5 consecutive delivery failures. Please update settings to re-enable.")

    save_webhook_history(history_data)

def dispatch_webhook(webhook_url: str, payload: Dict[str, Any], secret: str, doc_id: str, background_tasks = None):
    """
    Dispatches the webhook asynchronously.
    """
    if background_tasks:
        background_tasks.add_task(dispatch_webhook_sync, webhook_url, payload, secret, doc_id)
    else:
        import threading
        thread = threading.Thread(target=dispatch_webhook_sync, args=(webhook_url, payload, secret, doc_id))
        thread.start()
