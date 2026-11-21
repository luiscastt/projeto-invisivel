FROM node:24-bookworm-slim AS web
WORKDIR /build
COPY apps/web/package*.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM python:3.13-slim AS api
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/app/data OFFICIAL_DIR=/app/data/official
ENV PYTHONPATH=/app:/app/apps/api
COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --frozen --no-dev
COPY apps/api/ apps/api/
COPY pipelines/ pipelines/
COPY data/official/ data/official/
COPY --from=web /build/dist/ apps/web/dist/
RUN useradd --create-home --uid 10001 invisivel && mkdir -p data/uploads && chown -R invisivel:invisivel /app
USER invisivel
EXPOSE 8000
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
