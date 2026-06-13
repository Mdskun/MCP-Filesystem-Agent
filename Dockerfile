FROM python:3.11-slim

LABEL maintainer="your-email@example.com"
LABEL description="MCP Filesystem Agent - Token-optimized file management for Claude"
LABEL version="3.0.0"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY server_v3.py .

# Set environment variables
ENV MCP_BASE_DIR=/workspace
ENV PYTHONUNBUFFERED=1

# Create workspace directory
RUN mkdir -p /workspace

# Run the MCP server
CMD ["python", "server_v3.py"]
