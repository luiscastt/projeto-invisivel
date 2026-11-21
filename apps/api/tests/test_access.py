from conftest import login


def test_authentication_registration_and_permissions(client):
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/register", json={"email": "bad", "password": "x", "display_name": "X"}).status_code == 422
    r = client.post("/api/v1/auth/register", json={"email": "novo@example.com", "password": "Password!2026", "display_name": "Pessoa"})
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "citizen"
    assert "HttpOnly" in r.headers["set-cookie"]
    assert client.get("/api/v1/admin/moderation").status_code == 403
    assert client.get("/api/v1/auth/me").json()["display_name"] == "Pessoa"
    assert client.get("/api/v1/me/export").status_code == 200
    assert client.request("DELETE", "/api/v1/me", json={"password": "wrong"}).status_code == 403


def test_upstream_gaps_are_null_and_no_neighborhood_disaggregation(client):
    summary = client.get("/api/v1/territories/3205002/summary").json()
    assert summary["municipality"]["name"] == "Serra"
    assert summary["assessment"]["score"] is None
    assert summary["indicators"]
    assert all(i["value"] is None and i["granularity"] == "municipality" for i in summary["indicators"])
    assert client.get("/api/v1/states/35/municipalities").status_code == 404
    assert client.get("/api/v1/municipalities/3205002/neighborhoods").json() == []


def test_cross_origin_mutation_is_blocked(client):
    login(client)
    assert client.post("/api/v1/auth/logout", headers={"Origin": "https://hostil.example"}).status_code == 403


def test_auth_rate_limit_returns_retry_after(client):
    for _ in range(20):
        client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "Password!2026"})
    r = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "Password!2026"})
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"


def test_account_deletion_removes_session_and_votes(client, payload):
    from test_participation import publish
    issue_id = publish(client, payload)
    client.post("/api/v1/auth/register", json={"email": "delete@example.com", "password": "Password!2026", "display_name": "Excluir"})
    assert client.post(f"/api/v1/issues/{issue_id}/votes", json={"vote": "UNRESOLVED"}).status_code == 200
    result = client.request("DELETE", "/api/v1/me", json={"password": "Password!2026"})
    assert result.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(f"/api/v1/issues/{issue_id}/votes").json()["unresolved"] == 0


def test_official_source_cannot_be_a_private_publisher(client, payload):
    login(client)
    body = {**payload, "sources": [{"url": "https://example.com/claim", "title": "Falsa fonte oficial", "publisher": "Teste", "source_type": "official"}]}
    assert client.post("/api/v1/reports", json=body).status_code == 422
