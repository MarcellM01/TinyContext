FROM python:3.12-slim AS runtime-base

ARG TINYCONTEXT_VERSION=dev

LABEL org.opencontainers.image.title="TinyContext" \
      org.opencontainers.image.description="Token-light memory save and recall for local agents" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/MarcellM01/TinyContext" \
      org.opencontainers.image.version="${TINYCONTEXT_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TINYCONTEXT_VERSION=${TINYCONTEXT_VERSION} \
    TINYCONTEXT_MEMORY_DB_PATH=/data/memories.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin tinycontext \
    && mkdir -p /data \
    && chown -R tinycontext:tinycontext /data

USER tinycontext

FROM runtime-base AS fastapi

LABEL org.opencontainers.image.title="TinyContext FastAPI" \
      org.opencontainers.image.description="TinyContext HTTP API server"

EXPOSE 8000
VOLUME ["/data"]
CMD ["uvicorn", "servers.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime-base AS mcp

LABEL org.opencontainers.image.title="TinyContext MCP" \
      org.opencontainers.image.description="TinyContext MCP server"

VOLUME ["/data"]
CMD ["python", "servers/mcp_server.py"]
