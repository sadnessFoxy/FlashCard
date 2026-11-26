FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# Only the runtime dependencies from pyproject (cached layer), pinned to the versions the
# tests ran with. The code itself is not installed as a package: it runs from /app.
COPY pyproject.toml requirements.lock ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" > /tmp/requirements.txt \
    && pip install -c requirements.lock -r /tmp/requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY alembic.ini ./

RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/healthcheck.py || exit 1

# Behind the Caddy proxy: trust its X-Forwarded-For so rate limits see the real client IP.
# The API port is never published, so only Caddy can reach it.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
