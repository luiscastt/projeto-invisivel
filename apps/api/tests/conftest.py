import json
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    official = tmp_path / "official"
    official.mkdir()
    catalog = {"states": [{"code": "32", "name": "Espírito Santo", "abbreviation": "ES"}], "municipalities": [{"code": "3205002", "name": "Serra", "state_code": "32", "state_abbreviation": "ES", "center": [-40.3, -20.13]}, {"code": "3205309", "name": "Vitória", "state_code": "32", "state_abbreviation": "ES", "center": [-40.3, -20.3]}]}
    (official / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    (official / "geometry-3205002.json").write_text(json.dumps({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[-40.5, -20.25], [-40.1, -20.25], [-40.1, -19.9], [-40.5, -19.9], [-40.5, -20.25]]]}, "properties": {}}), encoding="utf-8")
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}", data_dir=tmp_path, official_dir=official, seed_demo=False, rate_limit=10000)
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def payload():
    return {"title": "Iluminação apagada na Rua das Flores", "description": "Os postes estão apagados há semanas na Rua das Flores, prejudicando a travessia da praça.", "category": "infrastructure", "state_code": "32", "municipality_code": "3205002", "neighborhood": "", "latitude": -20.13, "longitude": -40.3, "anonymous": True, "evidence_ids": [], "sources": [], "is_demo": False}


def login(client, admin=False):
    r = client.post("/api/v1/auth/login", json={"email": "admin@invisivel.local" if admin else "cidadao@invisivel.local", "password": "Invisivel!2026"})
    assert r.status_code == 200, r.text
    return r.json()["user"]
