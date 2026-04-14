# BUILDING STAGE
FROM python:3.12-slim-bookworm AS builder

# Define an argument to catch the version from env
ARG APP_VERSION=0.0.0

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation and copy mode for speed
ENV \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  SETUPTOOLS_SCM_PRETEND_VERSION=${APP_VERSION} \
  HATCH_VERSION=${APP_VERSION}

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  --mount=type=bind,source=apps,target=apps \
  --mount=type=bind,source=libs,target=libs \
  uv sync --frozen --no-install-project --no-dev

# Copy whole directory and run uv sync
COPY . .
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-editable


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
ENTRYPOINT ["example_app"]
