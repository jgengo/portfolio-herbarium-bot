FROM python:3.14.0b3-alpine3.21

# Install system dependencies for building Python packages
RUN apk add --no-cache \
    python3-dev \
    build-base \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    libjpeg-turbo-dev \
    libwebp-dev \
    tiff-dev \
    libde265-dev \
    libheif-dev \
    git

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