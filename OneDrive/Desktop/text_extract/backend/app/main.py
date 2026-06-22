import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import engine, Base
from .routers import documents, mappings, automation

# Create DB tables (if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(mappings.router, prefix=settings.API_V1_STR)
app.include_router(automation.router, prefix=settings.API_V1_STR)

# Serve uploaded documents & Playwright screenshots
# Create sub-folders if missing
os.makedirs(os.path.join(settings.UPLOAD_DIR, "screenshots"), exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Serve React frontend static files
from fastapi.responses import FileResponse
from fastapi import HTTPException

static_dist_path = os.path.abspath("static_dist")
if os.path.exists(static_dist_path):
    # Mount assets folder
    assets_path = os.path.join(static_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{catchall:path}")
    def serve_spa(catchall: str):
        # Allow FastAPI router to handle API and uploads static
        if catchall.startswith(settings.API_V1_STR[1:]) or catchall.startswith("static"):
            raise HTTPException(status_code=404)
            
        # Check if the requested file exists in static_dist (e.g. favicon.ico, logo.png)
        target_file = os.path.join(static_dist_path, catchall)
        if os.path.exists(target_file) and os.path.isfile(target_file):
            return FileResponse(target_file)
            
        # Fallback to index.html for virtual React browser routes
        index_file = os.path.join(static_dist_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="React build index.html not found.")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "service": settings.PROJECT_NAME,
            "ollama_url": settings.OLLAMA_BASE_URL,
            "slm_model": settings.OLLAMA_MODEL
        }
