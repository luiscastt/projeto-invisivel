import os
from pathlib import Path
import subprocess
import sys
import pytest
from pydantic import ValidationError
from app.config import Settings
from app.db import make_engine


def test_supabase_secret_never_enters_public_auth_config():
    with pytest.raises(ValidationError, match="publishable"):
        Settings(_env_file=None, supabase_anon_key="sb_secret_test-only")


def test_connection_and_storage_credentials_are_hidden_from_repr():
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://user:test-db-password@host/db", supabase_secret_key="test-storage-secret")
    assert "test-db-password" not in repr(settings)
    assert "test-storage-secret" not in repr(settings)


def test_database_schema_rejects_sql_fragments():
    with pytest.raises(ValueError, match="schema"):
        make_engine("sqlite://", schema='public; drop schema public')


def test_vercel_entrypoint_rejects_local_accounts_before_importing_application():
    root = Path(__file__).resolve().parents[3]
    env = {**os.environ, "VERCEL": "1", "VERCEL_ENV": "preview", "APP_ENV": "development"}
    result = subprocess.run([sys.executable, "-c", "import index"], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "require APP_ENV=production" in result.stderr


def test_serverless_origin_defaults_to_deployment_domain(monkeypatch):
    monkeypatch.setenv("VERCEL_URL", "invisivel-preview.vercel.app")
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.delenv("PUBLIC_ORIGIN", raising=False)
    settings = Settings(_env_file=None)
    assert settings.public_origin == "https://invisivel-preview.vercel.app"


def test_legacy_privileged_jwt_is_rejected_before_public_config():
    import base64, json
    payload = base64.urlsafe_b64encode(json.dumps({"role":"service_role"}).encode()).decode().rstrip("=")
    with pytest.raises(ValidationError, match="publishable|anon"):
        Settings(_env_file=None, supabase_anon_key="eyJhbGciOiJIUzI1NiJ9." + payload + ".test")


def test_postgres_defaults_to_dedicated_application_schema():
    assert Settings(_env_file=None).database_schema == "invisivel"


def test_validation_errors_do_not_echo_credentials():
    with pytest.raises(ValidationError) as rejected:
        Settings(_env_file=None, supabase_anon_key="sb_secret_synthetic", database_url="postgresql://test:synthetic-password@host/db")
    assert "sb_secret_synthetic" not in str(rejected.value)
    assert "synthetic-password" not in str(rejected.value)
