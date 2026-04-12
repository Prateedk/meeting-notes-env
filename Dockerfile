# Single-stage build from Python base to avoid openenv-base caching issues
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Copy project files
COPY . /app/env
WORKDIR /app/env

# Install dependencies
RUN uv sync --frozen --no-editable

# Gradio UI at /web; "/" redirects there (OpenEnv). Without this, HF Space homepage is 404.
ENV ENABLE_WEB_INTERFACE=true
ENV SPACE_ID=prateekdebit/meeting_notes_env

# Set PATH to use the virtual environment
ENV PATH="/app/env/.venv/bin:$PATH"

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH="/app/env:$PYTHONPATH"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port for HF Spaces
EXPOSE 8000

# Run the FastAPI server
CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 8000"]
