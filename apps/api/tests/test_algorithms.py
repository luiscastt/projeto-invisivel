from datetime import datetime, timezone
from decimal import Decimal

from app.algorithms import similarity, allocate, detect_flags


def test_duplicate_accent_normalization_and_municipal_boundary():
    a = dict(description="Iluminação apagada na rua das Flores", category="infrastructure", municipality_code="3205002", latitude=-20.13, longitude=-40.3, created_at=datetime.now(timezone.utc).isoformat())
    b = {**a, "description": "Iluminacao apagada na rua das flores"}
    assert similarity(a, b)["score"] >= .85
    assert similarity(a, {**b, "municipality_code": "3205309"})["score"] == 0
    assert similarity(a, {**b, "category": "sanitation"})["score"] < .85


def test_distant_same_text_is_not_a_strong_duplicate():
    a = dict(description="Postes apagados há semanas", category="infrastructure", municipality_code="3205002", latitude=-20.1, longitude=-40.3)
    assert similarity(a, {**a, "latitude": -20.3})["score"] < .65


def test_allocation_is_deterministic_exact_and_never_exceeds_budget():
    issues = [{"id": "a", "reports_count": 1}, {"id": "b", "reports_count": 4}]
    result = allocate(issues, Decimal("100.00"), Decimal("33.33"), "reports")
    assert result["capacity"] == 3
    assert result["issue_ids"] == ["b", "a"]
    assert result["spent"] == 66.66
    assert result["balance"] == 33.34
    assert allocate(issues, Decimal("100"), Decimal("33.33"), "reports") == result
    assert allocate([], Decimal("100"), Decimal("10"), "priority")["spent"] == 0


def test_flags_are_advisory_and_personal_data_is_queued():
    assert "possible_personal_data" in detect_flags("Contato: pessoa@example.com CPF 123.456.789-00")
    assert detect_flags("Há um buraco grande na rua, perto da praça.") == []
