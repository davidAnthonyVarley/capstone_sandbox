FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies, upgrade pip, and install Python packages in one layer
RUN apt-get update && \
    apt-get install -y build-essential curl git && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --upgrade pip aioquic

# Copy application code
COPY . /app

# Expose HTTP/3 port
EXPOSE 34433

# Default command
CMD ["python3", "http3_server.py"]