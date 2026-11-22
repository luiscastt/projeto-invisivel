"""Private evidence bytes, stored locally or in the configured Supabase bucket."""
import re

import httpx
from fastapi import HTTPException


UNAVAILABLE = "Serviço de arquivos indisponível. Tente novamente."


def _validate_path(path):
    if not isinstance(path, str) or not path or any(
        part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
        for part in path.split("/")
    ):
        raise HTTPException(422, "Caminho de evidência inválido.")


def _local_path(settings, path):
    root = settings.data_dir.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(422, "Caminho de evidência inválido.")
    return target


def _request(settings, method, path, *, content=None):
    bucket = settings.supabase_storage_bucket
    if not settings.supabase_secret_key or not settings.supabase_url or not re.fullmatch(r"[A-Za-z0-9_-]+", bucket):
        raise HTTPException(503, UNAVAILABLE)
    base = settings.supabase_url.rstrip("/") + "/storage/v1/object/"
    headers = {"apikey": settings.supabase_secret_key}
    if method == "DELETE":
        url = base + bucket
        kwargs = {"json": {"prefixes": [path]}}
    else:
        url = base + ("authenticated/" if method == "GET" else "") + bucket + "/" + path
        kwargs = {}
        if method == "POST":
            headers["Content-Type"] = "image/jpeg"
            kwargs["content"] = content
    try:
        response = httpx.request(method, url, headers=headers, timeout=20, follow_redirects=False, **kwargs)
    except httpx.HTTPError:
        raise HTTPException(503, UNAVAILABLE) from None
    if method == "GET" and response.status_code == 404:
        return None
    if not 200 <= response.status_code < 300:
        raise HTTPException(503, UNAVAILABLE)
    return response


def put_evidence(settings, path, content):
    _validate_path(path)
    if settings.storage_provider == "local":
        target = _local_path(settings, path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        except OSError:
            raise HTTPException(503, UNAVAILABLE) from None
    else:
        _request(settings, "POST", path, content=content)


def read_evidence(settings, path):
    _validate_path(path)
    if settings.storage_provider == "local":
        target = _local_path(settings, path)
        try:
            return target.read_bytes() if target.is_file() else None
        except OSError:
            raise HTTPException(503, UNAVAILABLE) from None
    response = _request(settings, "GET", path)
    return response.content if response is not None else None


def delete_evidence(settings, path):
    _validate_path(path)
    if settings.storage_provider == "local":
        try:
            _local_path(settings, path).unlink(missing_ok=True)
        except OSError:
            raise HTTPException(503, UNAVAILABLE) from None
    else:
        _request(settings, "DELETE", path)
