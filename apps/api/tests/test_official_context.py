import json
from pathlib import Path


def test_official_context_is_separate_from_community_issues(client, app):
    root = app.state.settings.official_dir
    (root / "cnes-3205002.json").write_text(json.dumps({"items": [{"id": "0000001", "name": "UBS teste", "category": "health", "latitude": -20.2, "longitude": -40.3, "attends_sus": True}], "total": 1, "complete": True, "fetched_at": "2026-11-20T00:00:00Z", "source_url": "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos", "notes": "Cadastro oficial"}), encoding="utf-8")
    (root / "schools-es.json").write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "id": "32000123", "properties": {"inep_id": "32000123", "municipality_code": "3205002", "name": "Escola estadual", "network": "state"}, "geometry": {"type": "Point", "coordinates": [-40.3, -20.2]}}]}), encoding="utf-8")
    r = client.get("/api/v1/territories/3205002/context")
    assert r.status_code == 200
    data = r.json()
    assert data["health"]["total"] == 1
    assert data["education"]["total"] == 1
    assert data["funding"]["available"] is False
    assert data["ombudsman"]["total"] is None
    assert client.get("/api/v1/issues").json()["total"] == 0
    features = client.get("/api/v1/territories/3205002/facilities").json()["features"]
    assert {f["properties"]["category"] for f in features} == {"health", "education"}


def test_sinisa_gzip_and_missing_financial_values(client, app):
    import gzip
    root = app.state.settings.official_dir
    record = {"municipality_code": "3205002", "responded": True, "reference_year": "2023", "information": [{"code": "OGM3004", "label": "Plano de saneamento", "value": "Sim"}], "indicators": [{"id": "sinisa_investment", "name": "Investimentos", "value": None, "sector": "sanitation", "unit": "R$", "year": "2023", "source_name": "SINISA", "source_url": "https://www.gov.br/cidades", "granularity": "municipality", "quality": "unavailable", "fetched_at": None}]}
    (root / "sinisa-municipalities.json.gz").write_bytes(gzip.compress(json.dumps({"3205002": record}).encode()))
    (root / "sinisa-manifest.json").write_text(json.dumps({"reference_year": "2023", "record_count": 1, "source_name": "SINISA Gestão Municipal", "source_url": "https://www.gov.br/cidades", "imported_at": "2026-11-20T00:00:00Z"}), encoding="utf-8")
    data = client.get("/api/v1/territories/3205002/context").json()
    assert data["sanitation_management"]["record"]["information"][0]["value"] == "Sim"
    values = client.get("/api/v1/territories/3205002/indicators").json()
    assert next(v for v in values if v["id"] == "sinisa_investment")["value"] is None


def test_public_ombudsman_only_aggregate_and_no_false_falabr_connection(client, app):
    root = app.state.settings.official_dir
    (root / "ombudsman-es.json").write_text(json.dumps({"year": "2025", "municipalities": {"3205002": {"total": 12, "by_type": {"Reclamação": 12}, "by_status": {"Encerrada": 12}}}, "quality": {"unmapped_rows": 3}, "source_url": "https://dados.es.gov.br"}), encoding="utf-8")
    data = client.get("/api/v1/territories/3205002/context").json()
    assert data["ombudsman"]["total"] == 12
    assert data["falabr"]["available"] is False
    assert data["falabr"]["authentication_required"] is True
    assert "Protocolo" not in json.dumps(data)


def test_wrong_official_coordinate_stays_in_list_but_not_map(client, app):
    root=app.state.settings.official_dir
    (root/'cnes-3205002.json').write_text(json.dumps({'items':[{'id':'123','name':'Unidade com ponto incorreto','category':'health','latitude':-21,'longitude':-41}],'total':1,'complete':True,'fetched_at':'2026-11-20','source_url':'https://apidadosabertos.saude.gov.br','notes':'Cadastro'}),encoding='utf8')
    assert client.get('/api/v1/territories/3205002/context').json()['health']['total']==1
    data=client.get('/api/v1/territories/3205002/facilities').json()
    assert data['features']==[]
    assert data['quality']['outside_boundary']==1


def test_failed_refresh_marks_retained_service_cache_stale(client, app):
    root=app.state.settings.official_dir
    (root/'cnes-3205002.json').write_text(json.dumps({'items':[],'total':0,'complete':True,'fetched_at':'2026-11-19','source_url':'https://apidadosabertos.saude.gov.br','notes':'Cadastro'}),encoding='utf8')
    (root/'services-manifest.json').write_text(json.dumps({'errors':[{'source':'cnes','municipality_code':'3205002','error_type':'TimeoutException'}]}),encoding='utf8')
    assert client.get('/api/v1/territories/3205002/context').json()['health']['stale'] is True
    source=next(s for s in client.get('/api/v1/sources').json() if s['id']=='cnes')
    assert source['stale'] is True
