FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir gradio && \
    pip install --no-cache-dir -e ".[llm]" 2>/dev/null || pip install --no-cache-dir -e .

# Copy app
COPY frontend/gradio/ ./

# Run application
CMD ["python", "app.py"]
