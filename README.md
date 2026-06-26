# Unitive Form Automation Platform (v0.1.0-alpha.1)

Welcome to the **Unitive Form Automation Platform** release `v0.1.0-alpha.1`. Unitive is an enterprise-grade, high-performance document ingestion, OCR parsing, and AI extraction engine designed to integrate seamlessly as a widget inside third-party ERP portals (such as SAP, NetSuite, Oracle, Zoho) and custom web portals.

This release implements a production-ready multi-tier Redis caching system, a secure Bearer session token authentication flow, an async jobs parsing engine, rate limiting, and an interactive security telemetry control board.

---

## 🚀 Alpha Release Checklist Status

### 1. Infrastructure & Telemetry
* **HTTPS**: Ready for TLS 1.3 protocol handshakes on ingress reverse proxies.
* **Separated Environments**: Decoupled database URLs, upload pathways, and models via `config.py` loading `.env` variables.
* **Redis Caching**: Configured multi-tier Redis caching (settings, API keys, duplicate detections, OCR fragments, AI structured extractions, and dashboard telemetry metrics) with automatic fallback to local memory cache.
* **PostgreSQL Native Compatibility**: Ready for standard SQLAlchemy database mappings; SQLite (`sql_app.db`) used for local debug, PostgreSQL recommended for production.
* **Health Handshakes**: Exposed public connection health check `/api/v1/admin/ping` returning `PONG`.
* **Telemetry Dashboard**: Tracks requests count, success/error rates, duplicate hits, and average processing latency in Redis.

### 2. Banking-Grade Security
* **API Key Hashing**: Cryptographically hashes API keys using SHA-256 in the database. Supports key rotation and multiple keys per workspace.
* **Embed Session Tokens**: Short-lived `uni_sess_` Bearer tokens issued via `/session/create` mapped in Redis to prevent key leakage in browser history or referrer headers.
* **Parent Origin Validation**: Validates host parent origins against session metadata during message exchanges.
* **Layered Rate Limits**: Layered Redis rate limiting restricting unauthenticated IPs (30 req/min) and individual workspace API keys (100 req/min).
* **Malware Quarantine Scan**: Simulates ClamAV file malware analysis during the quarantine ingestion phase.
* **File Signature Validation**: Restricts uploads to validated MIME types (`application/pdf`, `image/png`, `image/jpeg`, `image/tiff`) and file sizes (<20MB).
* **Feature Flags Config**: Configure flags per workspace to enable/disable OCR, AI, Autofill, Audit, and Virus Scanning.

### 3. Cognitive AI Pipeline
* **Prompt Versioning & Caching**: Bumping `prompt_version` in admin console automatically invalidates the `ai:result` caches.
* **OCR Fallbacks**: Preprocesses raw image uploads via OpenCV adaptive thresholding and falls back to heuristic line mapping if LLMs fail.
* **Confidence & Fallbacks**: Calculates extraction confidence ratings based on parsed keys and falls back gracefully to deterministic rule-based heuristic extraction if Ollama/Gemini is offline.

### 4. Shadow DOM SDK Integration
* **Shadow DOM Isolation**: Capsulates styling inside an isolated Shadow DOM tree to prevent stylesheet pollution with target host systems.
* **Offline Sync Queue**: Buffers uploads locally in localStorage during network outages and syncs automatically when reconnected.
* **Heartbeat Verification**: Continuous PING -> PONG connection check-ins; triggers floating reconnect banners when connection drops.
* **Rich Event Handlers**: Emit callbacks to the host parent, including `WidgetReady`, `AuthSuccess`, `OCRStarted`, `AIStarted`, `Complete`, `Error`, `Disconnected`, and `Reconnected`.

---

## 🛠️ Quick Start & Installation

### Backend Setup (FastAPI & Python 3.8+)
1. **Create and Activate Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. **Install Dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. **Configure Environment Variables**:
   Create a `.env` file inside `backend/` directory:
   ```env
   DATABASE_URL=sqlite:///./sql_app.db
   UPLOAD_DIR=./uploads
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=phi3
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
4. **Prepend Anaconda DLL Path (If SQLite dll errors occur)**:
   ```powershell
   $env:PATH = "C:\Folder F\Python\Library\bin;" + $env:PATH
   ```
5. **Launch Backend Dev Server**:
   ```powershell
   uvicorn backend.app.main:app --reload --port 8000
   ```

### Frontend Setup (Vite & React 18)
1. **Navigate to Frontend & Install Nodes**:
   ```powershell
   cd frontend
   npm install
   ```
2. **Compile Production Build assets**:
   ```powershell
   npm run build
   ```
3. **Sync Build Output to Backend Static Directory**:
   ```powershell
   Remove-Item -Path ../static_dist/* -Recurse -Force -ErrorAction SilentlyContinue
   Copy-Item -Path ./dist/* -Destination ../static_dist -Recurse -Force
   ```

---

## 📋 API Reference Summary

All requests to core endpoints under `/api/v1` require authorization headers: `Authorization: Bearer <API_KEY_OR_SESSION_TOKEN>`.

### 1. Webhook Handshakes & Sessions
* **Create Embed Token**: `POST /api/v1/admin/session/create`
  * Body: `{"api_key": "<Live Key>", "allowed_origin": "https://host-erp.com"}`
  * Returns: `{"session_token": "uni_sess_...", "expires_in_sec": 900}`
* **Verify SDK Compatibility**: `POST /api/v1/admin/sdk/negotiate`
  * Body: `{"sdk_version": "v1"}`
  * Returns: `{"status": "compatible"}`
* **Connection Heartbeat Check**: `GET /api/v1/admin/ping`
  * Returns: `{"status": "PONG"}`

### 2. Async Jobs Ingestion Pipeline
* **Create Async Job**: `POST /api/v1/documents/jobs/upload`
  * Form Data: `file: <File Binary>`
  * Returns: `{"job_id": "job_...", "status": "pending", "created_at": "..."}`
* **Get Job Stage**: `GET /api/v1/documents/jobs/{job_id}/status`
  * Returns: `{"job_id": "...", "status": "processing", "progress_stage": "ocr"}`
* **Fetch Job Result**: `GET /api/v1/documents/jobs/{job_id}/result`
  * Returns: `202 Accepted` (if processing) or `200 OK` containing `extracted_json` and `confidence_score`.

---

## 🔌 SDK Mounting Guide

Include the compiled SDK code in your ERP layout:
```html
<script src="http://localhost:8000/static/sdk/v1/mounter.js"></script>
<div id="unitive-automation-root"></div>

<script>
  UnitiveWidget.init({
    containerId: 'unitive-automation-root',
    sessionToken: 'uni_sess_902abc...', // Acquired backend-to-backend
    backendUrl: 'http://localhost:8000',
    theme: 'dark',
    onComplete: (res) => console.log('Extracted invoice fields:', res.extracted_json),
    onError: (err) => console.error('Error occurred:', err.message)
  });
</script>
```

---

## 🔔 Webhook Guide & Signature Verification

Upon job completion, the backend triggers an HTTP POST request to the `webhook_url` configured in your admin console settings.

### HMAC Signature Header
To guarantee request authenticity, the header `X-Signature` is attached, calculated as the SHA-256 HMAC of the stringified JSON request body using the configured `webhook_secret` key:
```javascript
const signature = crypto
  .createHmac('sha256', webhookSecret)
  .update(JSON.stringify(req.body))
  .digest('hex');
```

---

## ❓ FAQ & Troubleshooting

#### 1. Why does Python throw SQLite dll errors on Windows?
Ensure the Anaconda `Library\bin` path is added to your environment `PATH` variable when running. Run:
`$env:PATH = "C:\Folder F\Python\Library\bin;" + $env:PATH` before launching.

#### 2. What happens if the Redis server goes offline?
The cache layer catches the connection timeout (configured at 1.0 second) and automatically falls back to the simulated thread-safe `InMemoryCache`, preventing service locks.

---

## ⚠️ Known Issues (Alpha v0.1.0)
1. **ClamAV Integration**: The virus scanner runs as a simulated background check. Live containerized sockets need configuration inside `render.yaml` for production.
2. **Tabular Preprocessing**: Advanced invoice formats with skewed lines or multi-column grids require fine-tuning inside `ocr_engine.py` image adaptive thresholds.

---

## 🗺️ Roadmap & Next Milestones
* [ ] Integrate live ClamAV daemons inside Docker execution paths.
* [ ] Support database field encryption for highly sensitive customer metadata fields.
* [ ] Build distributed worker task processing queues using Celery/RabbitMQ to handle high-concurrency batch uploads.