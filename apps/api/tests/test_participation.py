import io
from PIL import Image
from conftest import login


def publish(client, payload):
    login(client)
    report = client.post("/api/v1/reports", json=payload)
    assert report.status_code == 201, report.text
    login(client, True)
    approved = client.post(f"/api/v1/admin/reports/{report.json()['id']}/approve", json={"reason": "Relato revisado para teste."})
    assert approved.status_code == 200, approved.text
    return approved.json()["issue_id"]


def test_pending_rejected_and_internal_records_are_private(client, payload):
    assert client.post("/api/v1/reports", json=payload).status_code == 401
    login(client)
    r = client.post("/api/v1/reports", json=payload)
    assert r.status_code == 201
    assert client.get("/api/v1/issues").json()["total"] == 0
    assert client.get("/api/v1/admin/moderation").status_code == 403
    login(client, True)
    assert client.post(f"/api/v1/admin/reports/{r.json()['id']}/reject", json={"reason": "Conteúdo rejeitado no teste."}).status_code == 200
    assert client.get("/api/v1/issues").json()["total"] == 0


def test_approval_vote_replacement_and_versioned_contribution(client, payload):
    issue_id = publish(client, payload)
    login(client)
    path = f"/api/v1/issues/{issue_id}"
    first = client.get(path).json()
    assert first["version"] == 1
    assert "email" not in client.get(path).text
    for _ in range(2):
        assert client.post(path + "/votes", json={"vote": "UNRESOLVED"}).json()["unresolved"] == 1
    votes = client.post(path + "/votes", json={"vote": "RESOLVED"}).json()
    assert (votes["resolved"], votes["unresolved"]) == (1, 0)
    assert client.get(path).json()["operational_status"] == "reported"
    assert client.delete(path + "/votes").json()["resolved"] == 0
    duplicate = client.post("/api/v1/reports/check-duplicates", json=payload).json()
    assert duplicate[0]["issue"]["id"] == issue_id
    new = {**payload, "description": payload["description"] + " A falta de luz também dificulta a passagem dos pedestres.", "existing_issue_id": issue_id}
    report_id = client.post("/api/v1/reports", json=new).json()["id"]
    assert client.get(path).json()["reports_count"] == 1
    login(client, True)
    client.post(f"/api/v1/admin/reports/{report_id}/approve", json={"reason": "Nova informação revisada.", "issue_id": issue_id}).raise_for_status()
    detail = client.get(path).json()
    assert detail["version"] == 2
    assert detail["reports_count"] == 2
    assert detail["reports"][0]["description"] == payload["description"]
    assert len(detail["updates"]) == 2
    assert client.post(path.replace("/issues/", "/admin/issues/") + "/restore", json={"version": 1, "reason": "Restaurando versão original."}).status_code == 200
    assert client.get(path).json()["version"] == 3


def test_territorial_validation_and_cross_municipality_link(client, payload):
    login(client)
    assert client.post("/api/v1/reports", json={**payload, "state_code": "35"}).status_code == 422
    assert client.post("/api/v1/reports", json={**payload, "latitude": -23}).status_code == 422
    assert client.post("/api/v1/reports", json={**payload, "neighborhood": "Bairro inexistente"}).status_code == 422
    assert client.post("/api/v1/reports", json={**payload, "sources": [{"url": "https://127.0.0.1/private", "title": "Fonte privada", "publisher": "Teste", "source_type": "community"}]}).status_code == 422
    issue_id = publish(client, payload)
    login(client)
    assert client.post("/api/v1/reports", json={**payload, "municipality_code": "3205309", "existing_issue_id": issue_id}).status_code == 422


def test_private_photo_is_only_public_after_approval_and_no_exif(client, payload):
    login(client)
    assert client.post("/api/v1/uploads", files={"file": ("evil.jpg", b"not an image", "image/jpeg")}).status_code == 422
    image = Image.new("RGB", (20, 20), "blue")
    raw = io.BytesIO()
    image.save(raw, "JPEG", exif=b"Exif\x00\x00secret")
    upload = client.post("/api/v1/uploads", files={"file": ("foto.jpg", raw.getvalue(), "image/jpeg")}, data={"caption": "Poste observado"})
    assert upload.status_code == 201, upload.text
    evidence_id = upload.json()["id"]
    client.post("/api/v1/auth/logout")
    assert client.get(f"/api/v1/media/{evidence_id}").status_code in (401, 404)
    issue_id = publish(client, {**payload, "evidence_ids": [evidence_id]})
    client.post("/api/v1/auth/logout")
    public_image = client.get(f"/api/v1/media/{evidence_id}")
    assert public_image.status_code == 200
    assert not Image.open(io.BytesIO(public_image.content)).getexif()
    assert client.get(f"/api/v1/issues/{issue_id}").json()["evidence_count"] == 1


def test_simulation_does_not_mutate_and_explains_assumptions(client, payload):
    issue_id = publish(client, payload)
    before = client.get(f"/api/v1/issues/{issue_id}").json()
    body = {"municipality_code": "3205002", "category": "infrastructure", "budget": 1000, "unit_cost": 333.33, "strategy": "priority", "demo": False}
    result = client.post("/api/v1/simulations", json=body).json()
    assert result["spent"] <= 1000
    assert result["selected_count"] == 1
    assert "hipotético" in result["disclaimer"].lower()
    assert client.get(f"/api/v1/issues/{issue_id}").json() == before
    assert client.get(f"/api/v1/simulations/{result['id']}").status_code == 200
    assert client.post("/api/v1/simulations", json={**body, "unit_cost": 0}).status_code == 422


def test_demo_is_separate_from_real_and_double_approval_conflicts(client, payload):
    issue_id = publish(client, {**payload, "is_demo": True})
    assert client.get("/api/v1/issues").json()["total"] == 0
    assert client.get("/api/v1/issues?demo=true").json()["total"] == 1
    assert client.get("/api/v1/territories/3205002/summary").json()["counts"]["total"] == 0
    report_id = client.get(f"/api/v1/issues/{issue_id}").json()["reports"][0]["id"]
    assert client.post(f"/api/v1/admin/reports/{report_id}/approve", json={"reason": "Aprovação repetida no teste."}).status_code == 409
