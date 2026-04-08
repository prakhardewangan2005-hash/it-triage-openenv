# ─────────────────────────────────────────────────────────────────────────────
# IT Helpdesk Triage OpenEnv — Dockerfile
# Builds a lean production image that starts the FastAPI server on port 7860.
# Compatible with Hugging Face Spaces (Docker SDK).
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL description="IT Helpdesk Triage & Incident Management — OpenEnv RL Environment"
LABEL version="1.0.0"

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY models.py environment.py app.py client.py inference.py openenv.yaml ./

# Transfer ownership to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Expose the port Hugging Face Spaces expects
EXPOSE 7860

# Health check so HF Space knows when the container is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/')"

# Launch the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", \
     "--workers", "1", "--log-level", "info"]
