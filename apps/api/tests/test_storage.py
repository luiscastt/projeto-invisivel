import io
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Evidence
from conftest import login


@pytest.fixture
def storage_settings(tmp_path):
    return SimpleNamespace(
        storage_provider="supabase", data_dir=tmp_path,
        supabase_url="https://storage.example.supabase.co",
        supabase_secret_key="sb_secret_test_never_expose",
        supabase_storage_bucket="invisivel-evidence",
    )


def test_local_storage_roundtrip_and_missing_file(storage_settings):
    from app.storage import put_evidence, read_evidence, delete_evidence
    storage_settings.storage_provider = "local"
    put_evidence(storage_settings, "uploads/photo.jpg", b"jpeg bytes")
    assert (storage_settings.data_dir / "uploads/photo.jpg").read_bytes() == b"jpeg bytes"
    assert read_evidence(storage_settings, "uploads/photo.jpg") == b"jpeg bytes"
    delete_evidence(storage_settings, "uploads/photo.jpg")
    delete_evidence(storage_settings, "uploads/photo.jpg")
    assert read_evidence(storage_settings, "uploads/photo.jpg") is None


def test_supabase_private_object_contract(storage_settings, monkeypatch):
    from app.storage import put_evidence, read_evidence, delete_evidence
    calls = []
    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return httpx.Response(200, content=b"jpeg bytes")
    monkeypatch.setattr("app.storage.httpx.request", request)
    put_evidence(storage_settings, "uploads/photo.jpg", b"jpeg bytes")
    assert read_evidence(storage_settings, "uploads/photo.jpg") == b"jpeg bytes"
    delete_evidence(storage_settings, "uploads/photo.jpg")
    base = storage_settings.supabase_url + "/storage/v1/object/"
    assert [(method, url) for method, url, _ in calls] == [
        ("POST", base + "invisivel-evidence/uploads/photo.jpg"),
        ("GET", base + "authenticated/invisivel-evidence/uploads/photo.jpg"),
        ("DELETE", base + "invisivel-evidence"),
    ]
    for _, _, kwargs in calls:
        assert kwargs["headers"]["apikey"] == storage_settings.supabase_secret_key
        assert "authorization" not in {key.lower() for key in kwargs["headers"]}
        assert kwargs["follow_redirects"] is False
        assert kwargs["timeout"] > 0
    assert calls[0][2]["headers"]["Content-Type"] == "image/jpeg"
    assert calls[0][2]["content"] == b"jpeg bytes"
    assert calls[2][2]["json"] == {"prefixes": ["uploads/photo.jpg"]}
    assert not (storage_settings.data_dir / "uploads").exists()


@pytest.mark.parametrize("provider", ["local", "supabase"])
@pytest.mark.parametrize("path", ["../secret.jpg", "/uploads/photo.jpg", "uploads/../photo.jpg", "uploads\\photo.jpg", "C:/photo.jpg", "uploads/photo.jpg?token=secret", "uploads//photo.jpg", "uploads/%2e%2e/photo.jpg"])
def test_unsafe_evidence_paths_are_rejected(storage_settings, monkeypatch, provider, path):
    from app.storage import put_evidence, read_evidence, delete_evidence
    storage_settings.storage_provider = provider
    def unexpected_request(*args, **kwargs):
        pytest.fail("Unsafe paths must not reach storage")
    monkeypatch.setattr("app.storage.httpx.request", unexpected_request)
    for operation in (lambda: put_evidence(storage_settings, path, b"photo"),
                      lambda: read_evidence(storage_settings, path),
                      lambda: delete_evidence(storage_settings, path)):
        with pytest.raises(HTTPException) as error:
            operation()
        assert error.value.status_code == 422


@pytest.mark.parametrize("operation", ["put", "read", "delete"])
@pytest.mark.parametrize("failure", ["transport", "upstream"])
def test_storage_failures_are_sanitized(storage_settings, monkeypatch, caplog, operation, failure):
    from app.storage import put_evidence, read_evidence, delete_evidence
    leaked = storage_settings.supabase_secret_key + " private-upstream-response"
    def request(*args, **kwargs):
        if failure == "transport":
            raise httpx.ConnectError(leaked)
        return httpx.Response(500, content=leaked.encode())
    monkeypatch.setattr("app.storage.httpx.request", request)
    operations = {"put": lambda: put_evidence(storage_settings, "uploads/photo.jpg", b"jpeg"),
                  "read": lambda: read_evidence(storage_settings, "uploads/photo.jpg"),
                  "delete": lambda: delete_evidence(storage_settings, "uploads/photo.jpg")}
    with pytest.raises(HTTPException) as error:
        operations[operation]()
    assert error.value.status_code == 503
    assert leaked not in str(error.value)
    assert storage_settings.supabase_secret_key not in str(error.value)
    assert leaked not in caplog.text


def test_missing_supabase_object_returns_none(storage_settings, monkeypatch):
    from app.storage import read_evidence
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(404))
    assert read_evidence(storage_settings, "uploads/missing.jpg") is None


def configure_supabase_storage(app):
    settings = app.state.settings
    settings.storage_provider = "supabase"
    settings.supabase_url = "https://storage.example.supabase.co"
    settings.supabase_secret_key = "sb_secret_test_never_expose"
    settings.supabase_storage_bucket = "invisivel-evidence"


def upload_photo(client):
    image = io.BytesIO()
    Image.new("RGB", (10, 10), "blue").save(image, "JPEG", exif=b"Exif\x00\x00private")
    result = client.post("/api/v1/uploads", files={"file": ("photo.jpg", image.getvalue(), "image/jpeg")})
    assert result.status_code == 201, result.text
    return result.json()["id"]


def test_supabase_media_keeps_authorization_and_private_bytes(client, app, monkeypatch, payload):
    from test_participation import publish
    configure_supabase_storage(app)
    objects = {}
    reads = []
    def request(method, url, **kwargs):
        path = url.split("/invisivel-evidence/")[-1]
        if method == "POST":
            objects[path] = kwargs["content"]
            return httpx.Response(200)
        reads.append(path)
        return httpx.Response(200, content=objects[path])
    monkeypatch.setattr("app.storage.httpx.request", request)
    login(client)
    evidence_id = upload_photo(client)
    assert not (app.state.settings.data_dir / "uploads").exists()
    owner = client.get(f"/api/v1/media/{evidence_id}")
    assert owner.status_code == 200
    assert not Image.open(io.BytesIO(owner.content)).getexif()
    client.post("/api/v1/auth/logout")
    reads.clear()
    assert client.get(f"/api/v1/media/{evidence_id}").status_code == 404
    assert reads == []
    client.post("/api/v1/auth/register", json={"email": "stranger@example.com", "password": "Password!2026", "display_name": "Pessoa"})
    assert client.get(f"/api/v1/media/{evidence_id}").status_code == 404
    assert reads == []
    login(client, True)
    assert client.get(f"/api/v1/media/{evidence_id}").status_code == 200
    publish(client, {**payload, "evidence_ids": [evidence_id]})
    client.post("/api/v1/auth/logout")
    public = client.get(f"/api/v1/media/{evidence_id}")
    assert public.status_code == 200
    assert public.headers["cache-control"] == "no-store"
    assert public.headers["content-type"] == "image/jpeg"
    assert public.headers["x-content-type-options"] == "nosniff"
    assert "storage.example" not in public.headers.get("location", "")


def test_supabase_media_missing_and_failure_are_sanitized(client, app, monkeypatch):
    configure_supabase_storage(app)
    login(client)
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(200))
    evidence_id = upload_photo(client)
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(404))
    assert client.get(f"/api/v1/media/{evidence_id}").status_code == 404
    secret = app.state.settings.supabase_secret_key
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(500, content=secret.encode()))
    result = client.get(f"/api/v1/media/{evidence_id}")
    assert result.status_code == 503
    assert secret not in result.text


def test_account_storage_cleanup_follows_commit_and_failure_is_sanitized(client, app, monkeypatch, caplog):
    configure_supabase_storage(app)
    login(client)
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(200))
    evidence_id = upload_photo(client)
    def fail_delete(settings, path):
        with Session(app.state.engine) as db:
            assert db.get(Evidence, evidence_id) is None
        raise HTTPException(503, settings.supabase_secret_key + " upstream-response")
    monkeypatch.setattr("app.security.delete_evidence", fail_delete)
    result = client.request("DELETE", "/api/v1/me", json={"password": "Invisivel!2026"})
    assert result.status_code == 200
    assert app.state.settings.supabase_secret_key not in caplog.text + result.text
    assert "upstream-response" not in caplog.text
    assert "órfão" in caplog.text


def test_retention_deletes_supabase_storage_only_after_commit(client, app, monkeypatch):
    from app.maintenance import cleanup
    configure_supabase_storage(app)
    user = login(client)
    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    with Session(app.state.engine) as db:
        db.add(Evidence(id="old-evidence", owner_id=user["id"], path="uploads/old.jpg", created_at=old))
        db.commit()
    calls = []
    def remove(settings, path):
        with Session(app.state.engine) as db:
            assert db.get(Evidence, "old-evidence") is None
        calls.append(path)
    monkeypatch.setattr("app.maintenance.delete_evidence", remove)
    assert cleanup(app.state.settings) == {"private_files_removed": 1}
    assert calls == ["uploads/old.jpg"]

@pytest.mark.parametrize("source", ["account", "retention"])
def test_failed_remote_deletion_is_durable_and_cleanup_retries_exact_path(client, app, monkeypatch, source):
    from app.maintenance import cleanup
    from app.models import StorageDeletion
    configure_supabase_storage(app)
    login(client)
    monkeypatch.setattr("app.storage.httpx.request", lambda *args, **kwargs: httpx.Response(200))
    evidence_id = upload_photo(client)
    path = f"uploads/{evidence_id}.jpg"
    if source == "retention":
        with Session(app.state.engine) as db:
            evidence = db.get(Evidence, evidence_id)
            evidence.created_at = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
            db.commit()
    calls = []
    failed = True
    def request(method, url, **kwargs):
        assert method == "DELETE"
        assert kwargs["json"] == {"prefixes": [path]}
        with Session(app.state.engine) as db:
            assert db.get(Evidence, evidence_id) is None
            assert db.scalar(select(StorageDeletion)).path == path
        calls.append(path)
        return httpx.Response(503 if failed else 200)
    monkeypatch.setattr("app.storage.httpx.request", request)
    if source == "account":
        assert client.request("DELETE", "/api/v1/me", json={"password": "Invisivel!2026"}).status_code == 200
    else:
        assert cleanup(app.state.settings) == {"private_files_removed": 0}
    with Session(app.state.engine) as db:
        pending = db.scalar(select(StorageDeletion))
        assert pending.path == path
        assert pending.id and pending.created_at
    failed = False
    assert cleanup(app.state.settings) == {"private_files_removed": 1}
    with Session(app.state.engine) as db:
        assert db.scalar(select(StorageDeletion)) is None
    assert calls == [path, path]
    assert cleanup(app.state.settings) == {"private_files_removed": 0}
    assert calls == [path, path]


def test_local_account_deletion_clears_file_and_pending_queue(client, app):
    from app.models import StorageDeletion
    login(client)
    evidence_id = upload_photo(client)
    path = app.state.settings.data_dir / f"uploads/{evidence_id}.jpg"
    assert path.is_file()
    assert client.request("DELETE", "/api/v1/me", json={"password": "Invisivel!2026"}).status_code == 200
    assert not path.exists()
    with Session(app.state.engine) as db:
        assert db.scalar(select(StorageDeletion)) is None
