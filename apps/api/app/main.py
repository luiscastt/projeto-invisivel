from contextlib import asynccontextmanager
from collections import defaultdict, deque
import asyncio
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .config import Settings, ROOT
from .db import Base, make_engine
from . import models, security, territories, issues, moderation, uploads, simulations, official_context
from .seed import bootstrap
from .http_limits import RequestSizeLimit

log = logging.getLogger("invisivel")


def create_app(settings=None):
    settings = settings or Settings()
    settings.check_production()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            bootstrap(db, settings)
            db.commit()
        yield
        engine.dispose()

    app = FastAPI(title="INVISIVEL — API pública", version="0.1.0", description="Inteligência territorial com proveniência, participação moderada e simulações hipotéticas. Dados pessoais e pendências não são públicos.", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.engine, app.state.settings = engine, settings
    app.add_middleware(RequestSizeLimit)
    windows = defaultdict(deque)
    sqlite_write_lock = asyncio.Lock()

    @app.middleware("http")
    async def protections(request, call_next):
        started = time.monotonic()
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        mutating = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        if mutating:
            origin = request.headers.get("origin")
            allowed = {settings.public_origin.rstrip("/"), "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"} if settings.app_env != "production" else {settings.public_origin.rstrip("/")}
            if origin and origin.rstrip("/") not in allowed:
                return JSONResponse({"detail": "Origem da requisição não permitida."}, status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site" and not request.headers.get("authorization", "").startswith("Bearer "):
                return JSONResponse({"detail": "Requisição entre sites bloqueada."}, status_code=403)
        limit = settings.rate_limit
        bucket = "public"
        if path.startswith("/api/v1/auth/") and mutating:
            limit, bucket = min(limit, 20), "auth"
        elif path.endswith("/sync"):
            limit, bucket = 2, "sync"
        elif mutating and not path.startswith("/api/v1/simulations"):
            limit, bucket = min(limit, 60), "participation"
        key = (ip, bucket)
        current = windows[key]
        while current and current[0] < started - 60:
            current.popleft()
        if path.startswith("/api/") and len(current) >= limit:
            return JSONResponse({"detail": "Muitas solicitações. Aguarde um minuto."}, status_code=429, headers={"Retry-After": "60"})
        if path.startswith("/api/"):
            current.append(started)
        if len(windows) > 10000:
            for k in [k for k, v in windows.items() if not v or v[-1] < started - 60]:
                windows.pop(k, None)
        # SQLite has no SELECT FOR UPDATE; serialize mutations within local single worker.
        if mutating and settings.database_url.startswith("sqlite"):
            async with sqlite_write_lock:
                response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Avoid reflecting submitted passwords or private report text in validation errors.
        messages = [f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
        return JSONResponse({"detail": "; ".join(messages)}, status_code=422)

    @app.exception_handler(IntegrityError)
    async def conflict(request, exc):
        return JSONResponse({"detail": "Este registro foi alterado por outra solicitação. Atualize e tente novamente."}, status_code=409)

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(request, exc):
        log.error("Falha de persistência: %s", type(exc).__name__)
        return JSONResponse({"detail": "Não foi possível confirmar a gravação. Tente novamente quando o banco estiver disponível."}, status_code=503)

    @app.get("/api/v1/health", tags=["Operação"])
    def health():
        return {"status": "ok", "environment": settings.app_env, "version": "0.1.0"}

    for router in [security.router, security.account_router, territories.router, official_context.router, issues.router, moderation.router, uploads.router, simulations.router]:
        app.include_router(router, prefix="/api/v1")

    # Built frontend can be served by one process for local review/containers.
    dist = ROOT / "apps/web/dist"
    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        from fastapi import HTTPException
        if path.startswith("api/"):
            raise HTTPException(404, "Endpoint não encontrado.")
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})
        raise HTTPException(404, "Frontend ainda não compilado. Execute npm run build em apps/web.")
    return app


app = create_app()
