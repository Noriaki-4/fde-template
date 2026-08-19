FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .

# Install Python dependencies (core deps + mcp extras)
RUN pip install --no-cache-dir -e ".[mcp]"

# Copy app
COPY mcp-server/ ./

# Health check — Streamable HTTP is a JSON-RPC endpoint, not a REST /health
# route, so a plain TCP connect is the reliable "is it listening" check.
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8200), timeout=3)" || exit 1

# Run application
CMD ["python", "server.py"]
