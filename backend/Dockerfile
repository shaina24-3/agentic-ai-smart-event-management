FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# No additional system dependencies required

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and document knowledge base
COPY app /app/app

# Expose FastAPI application port
EXPOSE 8000

# Default runner command using uvicorn.
# Render injects a PORT environment variable that the container MUST bind to;
# it falls back to 8000 for local docker-compose where PORT is unset.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]