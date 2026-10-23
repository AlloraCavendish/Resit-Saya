# Purpose: Container build specification for Resit Saya FastAPI backend.
# Security: Minimal base image, installs only runtime dependencies, sets up persistent volume paths.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build-essential, curl for health checks if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir .

# Copy application source code
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

# Create data and uploads directories
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
