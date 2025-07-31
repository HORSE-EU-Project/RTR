# Use Ubuntu as base image for better compatibility
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and install llama-cpp-python with server support
RUN pip3 install --upgrade pip
RUN pip3 install llama-cpp-python[server] --verbose

# Create models directory
RUN mkdir -p /models

# Copy models (if any exist)
COPY models/ /models/

# Environment variables for configuration
ENV MODEL=/models/gemma-2-2b-it-Q4_K_M.gguf
ENV HOST=0.0.0.0
ENV PORT=8080
ENV N_CTX=2048
ENV N_THREADS=4

# Expose the port (using 8080 to avoid conflict with RTR API)
EXPOSE 8080

# Create a health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8080/v1/models || exit 1' > /app/health_check.sh && \
    chmod +x /app/health_check.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/health_check.sh

# Start the llama-cpp-python server
CMD python3 -m llama_cpp.server \
    --model ${MODEL} \
    --host ${HOST} \
    --port ${PORT} \
    --n_ctx ${N_CTX} \
    --n_threads ${N_THREADS}
