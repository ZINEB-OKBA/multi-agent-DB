FROM python:3.13-slim

# Install system dependencies (like build-essential for compiling some dependencies if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app/backend

# Copy requirements file from backend subdirectory (which contains all requirements including fastapi, langchain, etc.)
COPY backend/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the FastAPI application using uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
