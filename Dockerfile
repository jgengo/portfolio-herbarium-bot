FROM python:3.13-slim

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libwebp-dev \
    libtiff-dev \
    libde265-dev \
    libheif-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configure Git for the container
RUN git config --global user.email "jordane.gengo@gmail.com" && \
    git config --global user.name "Herbarium Bot"

# Install uv CLI for dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install Python dependencies based on pyproject.toml and uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync

# Copy the application source code
COPY . .

# Default command to run the bot
CMD ["uv", "run", "python", "-m", "herbabot.main"]