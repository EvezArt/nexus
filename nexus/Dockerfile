FROM python:3.11-slim

LABEL maintainer="Morpheus <morpheus@evez.ai>"
LABEL description="NEXUS — Unified 24/7 chatbot connecting ChatGPT, Perplexity, and OpenClaw"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (minimal — httpx only)
RUN pip install --no-cache-dir httpx

# Copy nexus
COPY nexus/ ./nexus/
COPY morpheus_spine.py ./
COPY morpheus_local.py ./

# Create directories
RUN mkdir -p nexus/memory soul/cognition

# Environment
ENV PYTHONUNBUFFERED=1
ENV MORPHEUS_WORKSPACE=/app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import pathlib; p=pathlib.Path('/app/nexus/daemon.pid'); exit(0 if p.exists() else 1)"

# Default: run daemon in serve mode
EXPOSE 8877

CMD ["python3", "nexus/nexus_daemon.py", "--interval", "300", "--serve", "--port", "8877"]
