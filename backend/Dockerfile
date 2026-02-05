FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy configuration
COPY pyproject.toml ./

# Configure poetry to not create virtual env (install globally)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy source code
COPY . .

# Add src to PYTHONPATH so uvicorn can find the module
ENV PYTHONPATH=/app/src

# Run application
CMD ["uvicorn", "scout.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

