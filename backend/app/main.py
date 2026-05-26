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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "slm_model": settings.OLLAMA_MODEL
    }
