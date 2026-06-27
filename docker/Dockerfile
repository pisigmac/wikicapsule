FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency specification
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN uv pip install --system -e ".[dev]"

# Download sentence transformer model at build time for faster startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Environment
ENV WIKICAPSULE_WIKI_DIR=/wiki
ENV WIKICAPSULE_TRANSPORT=stdio
ENV WIKICAPSULE_LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Create wiki directory
RUN mkdir -p /wiki

# Entry point
ENTRYPOINT ["python", "-m", "wikicapsule.server"]

# Expose port for SSE mode
EXPOSE 8080
