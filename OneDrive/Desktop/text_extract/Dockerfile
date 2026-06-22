# Stage 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend config files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source files and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Package Backend and Serve Frontend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for Playwright and OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    glib-2.0 \
    libgl1-mesa-glx \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
# Using CPU-only PyTorch to minimize image size and fit RAM constraints on Render/Railway
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Install Playwright browser and dependencies
RUN playwright install chromium

# Copy React frontend build files from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./static_dist

# Copy FastAPI backend application code
COPY backend/app ./app

# Create necessary storage directories
RUN mkdir -p storage/uploads/screenshots

# Set default production environment variables
ENV UPLOAD_DIR=/app/storage/uploads
ENV DATABASE_URL=sqlite:////app/storage/sql_app.db
ENV PLAYWRIGHT_HEADLESS=True

EXPOSE 8000

# Run FastAPI using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
