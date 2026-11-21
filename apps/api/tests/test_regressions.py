import json
import pytest
from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Report, User
from conftest import login


def test_built_frontend_same_origin_login(client):
    result = client.post("/api/v1/auth/login", json={"email": "cidadao@invisivel.local", "password": "Invisivel!2026"}, headers={"Origin": "http://127.0.0.1:8000"})
    assert result.status_code == 200


def test_supabase_grants_follow_current_verified_email(client, app, monkeypatch):
    settings = app.state.settings
    settings.auth_provider = "supabase"
    settings.supabase_url = "https://identity.supabase.co"
    settings.admin_emails = "staff@example.com"
    info = {"id": "supabase-user", "email": "staff@example.com", "email_confirmed_at": "2026-11-20T00:00:00Z", "user_metadata": {"display_name": "Equipe", "role": "admin"}}
    monkeypatch.setattr("app.security.httpx.get", lambda *a, **kw: SimpleNamespace(raise_for_status=lambda: None, json=lambda: info))
    headers = {"Authorization": "Bearer example-token"}
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "admin"
    settings.admin_emails = "new-staff@example.com"
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "citizen"
    info["email"] = "other@example.com"
    assert client.get("/api/v1/auth/me", headers=headers).json()["email"] == "other@example.com"


def test_deletion_purges_unpublished_location_and_original(client, app, payload):
    login(client)
    report_id = client.post("/api/v1/reports", json=payload).json()["id"]
    result = client.request("DELETE", "/api/v1/me", json={"password": "Invisivel!2026"})
    assert result.status_code == 200
    with Session(app.state.engine) as db:
        report = db.get(Report, report_id)
        assert "latitude" not in report.payload
        assert "longitude" not in report.payload
        assert "occurrence_date" not in report.payload
        assert "evidence_ids" not in report.payload
        assert payload["description"] not in json.dumps(report.payload)


def test_national_population_and_failure_provenance(client, app):
    directory = app.state.settings.official_dir
    (directory / "population-national.json").write_text(json.dumps({"3205002": 520653}), encoding="utf-8")
    (directory / "sources.json").write_text(json.dumps([{"id": "ibge-censo-populacao-nacional", "status": "active", "notes": "Dados do Censo.", "last_synced": "2026-11-20T00:00:00Z"}]), encoding="utf-8")
    (directory / "ingestion-manifest.json").write_text(json.dumps({"status": "failed", "errors": [{"job": "population"}]}), encoding="utf-8")
    values = client.get("/api/v1/territories/3205002/indicators").json()
    population = next(i for i in values if i["id"] == "population")
    assert population["value"] == 520653 and population["year"] == "2022"
    assert client.get("/api/v1/sources").json()[0]["stale"] is True


@pytest.mark.parametrize("url", ["https://example.com\\.gov.br/not-official", "https://example.com%5c.gov.br/path", "https://example.com/space in path"])
def test_browser_ambiguous_urls_are_rejected(client, payload, url):
    login(client)
    body = {**payload, "sources": [{"url": url, "title": "Fonte de referência", "publisher": "Teste", "source_type": "official"}]}
    assert client.post("/api/v1/reports", json=body).status_code == 422


def test_commit_failure_never_returns_success(client, monkeypatch):
    from sqlalchemy.exc import OperationalError
    def fail(self):
        raise OperationalError("COMMIT", {}, Exception("database unavailable"))
    monkeypatch.setattr(Session, "commit", fail)
    r = client.post("/api/v1/auth/register", json={"email": "failure@example.com", "password": "Password!2026", "display_name": "Falha"})
    assert r.status_code == 503


def test_clarification_has_an_immutable_citizen_reply(client, payload):
    login(client)
    report_id = client.post("/api/v1/reports", json=payload).json()["id"]
    login(client, True)
    assert client.post(f"/api/v1/admin/reports/{report_id}/clarify", json={"reason": "Informe se o ponto corresponde à travessia."}).status_code == 200
    login(client)
    r = client.post(f"/api/v1/me/reports/{report_id}/reply", json={"description": "O ponto indicado corresponde à travessia ao lado da praça."})
    assert r.status_code == 201
    login(client, True)
    row = next(r for r in client.get("/api/v1/admin/moderation").json() if r["id"] == report_id)
    assert row["description"] == payload["description"]
    assert row["clarifications"][0]["description"].startswith("O ponto indicado")


def test_body_limit_precedes_multipart_parsing(client):
    assert client.post("/api/v1/uploads", content=b"x", headers={"Content-Length": str(7 * 1024 * 1024)}).status_code == 413


def test_static_shell_requests_do_not_exhaust_api_rate_limit(client, app):
    app.state.settings.rate_limit = 5
    for _ in range(8):
        assert client.get("/marca.svg").status_code != 429
    for _ in range(5):
        assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 429


def test_evidence_can_be_withdrawn_without_erasing_history(client, payload):
    import io
    from PIL import Image
    from test_participation import publish
    login(client)
    image = io.BytesIO()
    Image.new("RGB", (10, 10)).save(image, "JPEG")
    evidence_id = client.post("/api/v1/uploads", files={"file": ("photo.jpg", image.getvalue(), "image/jpeg")}).json()["id"]
    issue_id = publish(client, {**payload, "evidence_ids": [evidence_id]})
    assert client.post(f"/api/v1/admin/evidence/{evidence_id}/withdraw", json={"reason": "Revisão de privacidade na imagem."}).status_code == 200
    client.post("/api/v1/auth/logout")
    assert client.get(f"/api/v1/media/{evidence_id}").status_code == 404
    detail = client.get(f"/api/v1/issues/{issue_id}").json()
    assert detail["evidence_count"] == 0
    assert detail["version"] == 2
    assert detail["updates"][-1]["update_type"] == "evidence_withdrawn"
