# BUILDING STAGE
FROM python:3.12-slim-bookworm AS builder

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation and copy mode for speed
ENV \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=.,target=. \
  uv sync --frozen --no-install-project --no-dev

# Copy whole directory and run uv sync
COPY . .
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev


# RUNTIME STAGE
FROM python:3.12-slim-bookworm

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with correct ownership
COPY --chown=appuser:appuser apps/example_app ./apps/example_app
COPY --chown=appuser:appuser pyproject.toml .

# Environment configuration
ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

USER appuser

# Set the command to run your app
CMD ["python", "-m", "example_app.main"]
