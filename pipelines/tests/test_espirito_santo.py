import json

import pytest

from pipelines import espirito_santo


CATALOG = {
    "municipalities": [
        {"code": "3205002", "name": "Serra", "state_abbreviation": "ES"},
        {"code": "3205309", "name": "Vitória", "state_abbreviation": "ES"},
        {"code": "2616209", "name": "Vitória", "state_abbreviation": "PE"},
    ]
}


def school(**changes):
    return {
        "nm_regional": "Regional",
        "nm_municipio": "  VITORIA ",
        "inep_escola": "32012345",
        "nm_escola": "Escola Estadual",
        "latitude": "-20,32",
        "longitude": "-40,31",
        **changes,
    }


def manifestation(**changes):
    return {
        "Ano": 2025,
        "Municipio": "Vitória",
        "TipoManifestacao": "Solicitação",
        "Situacao": "Encerrada",
        "Protocolo": 999999999,
        "Assunto": "Rótulo reservado",
        **changes,
    }


def test_school_preserves_inep_as_string_and_maps_official_coordinates():
    result = espirito_santo.normalize_schools([school()], CATALOG)

    assert result["type"] == "FeatureCollection"
    assert result["features"] == [{
        "type": "Feature",
        "id": "32012345",
        "geometry": {"type": "Point", "coordinates": [-40.31, -20.32]},
        "properties": {
            "inep_id": "32012345",
            "name": "Escola Estadual",
            "municipality_code": "3205309",
            "network": "state",
            "source_name": "SEDU-ES",
            "source_url": espirito_santo.SCHOOLS_SOURCE_URL,
        },
    }]


@pytest.mark.parametrize("coordinates", [
    {"latitude": "NaN"},
    {"longitude": -181},
    {"latitude": 999},
    {"latitude": -7.23835},
    {"latitude": 0, "longitude": 0},
    {"latitude": None},
    {"latitude": "-40,31", "longitude": "-20,32"},
])
def test_school_keeps_official_record_without_invalid_point(coordinates):
    result = espirito_santo.normalize_schools([school(**coordinates)], CATALOG)

    assert len(result["features"]) == 1
    assert result["features"][0]["geometry"] is None


def test_school_requires_unambiguous_identification():
    result = espirito_santo.normalize_schools([
        school(), school(nm_municipio="Outra UF"), school(inep_escola="--"),
        school(nm_escola=""),
    ], CATALOG)

    assert [feature["id"] for feature in result["features"]] == ["32012345"]


def test_school_rejects_conflicting_records_with_same_inep_code():
    with pytest.raises(ValueError):
        espirito_santo.normalize_schools([school(), school(nm_municipio="Serra")], CATALOG)


def test_ombudsman_counts_only_2025_es_municipalities_and_public_categories():
    rows = [
        manifestation(),
        manifestation(Ano="2025", Municipio="  VITORIA ", TipoManifestacao="Reclamação", Situacao=""),
        manifestation(Municipio="Serra", TipoManifestacao=None, Situacao="Em tratamento"),
        manifestation(Ano=2026),
        manifestation(Municipio="Todo Estado"),
        manifestation(Municipio="Vitória de Santo Antão"),
        manifestation(Municipio=None),
    ]

    result = espirito_santo.normalize_ombudsman(rows, CATALOG)

    assert result["municipalities"] == {
        "3205002": {
            "year": "2025", "total": 1,
            "by_type": {"Não informado": 1}, "by_status": {"Em tratamento": 1},
        },
        "3205309": {
            "year": "2025", "total": 2,
            "by_type": {"Reclamação": 1, "Solicitação": 1},
            "by_status": {"Encerrada": 1, "Não informado": 1},
        },
    }
    assert result["year"] == "2025"
    assert result["quality"] == {
        "accepted_rows": 3, "unmapped_rows": 3, "ignored_year_rows": 1, "total_rows": 7,
    }
    serialized = json.dumps(result, ensure_ascii=False)
    assert "999999999" not in serialized
    assert "Rótulo reservado" not in serialized
