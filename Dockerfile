FROM python:3.11-slim

LABEL maintainer="manthandsoni@gmail.com"
LABEL description="MCP Filesystem Agent - Token-optimized file management for Claude"
LABEL version="3.0.0"
LABEL org.opencontainers.image.source="https://github.com/Mdskun/mcp-fs-agent"

WORKDIR /app

# procps provides pgrep, used by the HEALTHCHECK below
RUN apt-get update && \
    apt-get install -y --no-install-recommends procps && \
    rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN useradd -m -u 1000 mcp && \
    mkdir -p /workspace && \
    chown -R mcp:mcp /workspace

# Install dependencies
COPY --chown=mcp:mcp requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copy the application
COPY --chown=mcp:mcp server3.py .

# Set environment variables
ENV MCP_BASE_DIR=/workspace \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

# Expose port for monitoring
EXPOSE 8000

# Switch to non-root user
USER mcp

# Health check: verify the server3.py process is actually running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "python.*server3.py" > /dev/null || exit 1

# Run the MCP server
CMD ["python", "server3.py"]
