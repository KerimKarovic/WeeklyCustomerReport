FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Production stage
FROM base AS production

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user and set up directories
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p output/reports output/test-pdfs && \
    chown -R app:app /app

USER app

# Copy application code
COPY --chown=app:app . .

# Default command
CMD ["python", "app/main.py"]

# Development stage
FROM base AS development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user and set up directories
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p output/reports output/test-pdfs && \
    chown -R app:app /app

USER app

# Copy application code
COPY --chown=app:app . .

# Default command for development
CMD ["python", "app/main.py", "--mode", "preview"]


