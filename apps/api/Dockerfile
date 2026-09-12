FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (libgomp1 required for XGBoost openmp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app, ml pipeline artifacts, scripts, and seed data
COPY apps/api /app
COPY ml /app/ml
COPY scripts /app/scripts
COPY data /app/data

EXPOSE 8000

CMD ["sh", "-c", "python scripts/seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
