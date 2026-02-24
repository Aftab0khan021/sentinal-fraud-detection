FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install additional tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    jq \
    htop \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    black \
    flake8 \
    mypy \
    pytest-watch \
    pre-commit

# Set working directory
WORKDIR /workspace

# Keep container running
CMD ["sleep", "infinity"]
