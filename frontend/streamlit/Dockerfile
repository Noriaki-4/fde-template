FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir streamlit && \
    pip install --no-cache-dir -e ".[llm]" 2>/dev/null || pip install --no-cache-dir -e .

# Copy app
COPY frontend/streamlit/ ./

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Run application
CMD ["streamlit", "run", "app.py"]
