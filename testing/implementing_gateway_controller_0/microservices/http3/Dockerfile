FROM python:3.11-slim

# Install pip and build essentials
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install aioquic
RUN python -m pip install aioquic

# Set working directory
WORKDIR /app

# Copy your code
COPY . /app

# Expose HTTP/3 port
EXPOSE 4433

# Default command
CMD ["python3", "http3_server.py"]


