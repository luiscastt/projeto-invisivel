from __future__ import annotations

import hashlib
import json

import pytest

from pipelines.connectors import OfficialSource
from pipelines.sync import URLS, run_sync


PILOTS = {"3205002": 520653, "3205309": 322869}
MESH = {"type": "Polygon", "coordinates": [[[-40, -20], [-39, -20], [-39, -19], [-40, -20]]]}
FETCHED_AT = "2026-11-21T01:20:00Z"


def aggregate(identifier, unit, values, classifications=()):
    return [{
        "id": str(identifier),
        "unidade": unit,
        "resultados": [{
            "classificacoes": list(classifications),
            "series": [
                {"localidade": {"id": code}, "serie": {"2022": str(value)}}
                for code, value in values.items()
            ],
        }],
    }]


def feature(properties):
    return {"type": "Feature", "properties": properties, "geometry": MESH}


def survey(identifier, year, values):
    return {
        "id": identifier,
        "res": [
            {"localidade": code[:6], "res": {year: str(value)}}
            for code, value in zip(PILOTS, values, strict=True)
        ],
    }


class FixtureSource:
    def __init__(self):
        self.failures = set()
        local = {str(code): code for code in range(1100000, 1105500)}
        local.update(PILOTS)
        self.payloads = {
            "states": [{"id": code, "nome": f"UF {code}", "sigla": f"U{code}"} for code in range(11, 38)],
            "municipalities": [{"id": int(code), "nome": f"Município {code}"} for code in local],
            "population": aggregate(93, "Pessoas", PILOTS),
            "population-national": aggregate(93, "Pessoas", local),
            "surveys": [
                survey(60045, "2022", (98.34, 99.24)),
                survey(30279, "2025", (11.74, 10.54)),
                survey(29171, "2026", (586901, 343935)),
            ],
            "sanitation": aggregate(1000381, "Percentual", dict(zip(PILOTS, (91.23, 99.67), strict=True)), (
                {"id": "11558", "categoria": {"46290": "Rede geral, rede pluvial ou fossa ligada à rede"}},
            )),
            **{
                f"geometry-{code}": {"type": "FeatureCollection", "features": [feature({"codarea": code})]}
                for code in PILOTS
            },
            "neighborhoods-3205002": {"type": "FeatureCollection", "features": [
                feature({"tx_bairro": "Área Rural", "pk_bairro_ctm": None, "objectid": 106}),
                feature({"tx_bairro": "Centro", "pk_bairro_ctm": 77, "objectid": 28}),
            ]},
            "neighborhoods-3205309": {"type": "FeatureCollection", "features": [
                feature({"nome": "Centro", "codBairro": 321}),
                feature({"nome": "Praia do Canto", "codBairro": 123}),
            ]},
        }

    def fetch(self, url):
        job = next(job for job, target in URLS.items() if url == target)
        if job in self.failures:
            raise RuntimeError("upstream indisponível")
        payload = self.payloads[job]
        raw = json.dumps(payload).encode()
        return payload, {
            "url": url, "fetched_at": FETCHED_AT,
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
        }


def read(path, filename):
    return json.loads((path / filename).read_bytes())


def test_sync_normalizes_pilot_snapshot_and_national_population(tmp_path):
    report = run_sync(tmp_path, source=FixtureSource())

    assert report["status"] == "completed"
    assert len(report["files"]) == 9
    assert all(len(job["sha256"]) == 64 for job in report["jobs"])
    assert len(read(tmp_path, "catalog.json")["municipalities"]) == 5502
    assert read(tmp_path, "population-national.json")["3205309"] == 322869
    assert read(tmp_path, "geometry-3205002.json")["features"][0]["properties"]["codarea"] == "3205002"
    neighborhoods = read(tmp_path, "neighborhoods-3205002.json")
    assert any(row["id"] == "3205002-obj-106" and row["geometry_status"] == "official" for row in neighborhoods)
    serra = {row["id"]: row for row in read(tmp_path, "indicators-3205002.json")}
    assert serra["sewage_network"]["value"] == 91.23
    assert serra["sewage_network"]["unit"] == "%"
    assert serra["schooling"]["year"] == "2022"
    assert serra["infant_mortality"]["value"] == 11.74
    sources = {source["id"]: source for source in read(tmp_path, "sources.json")}
    assert sources["ibge-censo-populacao-nacional"]["status"] == "active"
    assert sources["ibge-censo-populacao-nacional"]["records"] == 5502
    assert sources["inep-censo-escolar"]["status"] == "requires_configuration"
    assert sources["portal-transparencia"]["status"] == "requires_configuration"
    assert sources["fala-br"]["status"] == "requires_configuration"


def test_failed_core_validation_preserves_all_previous_artifacts(tmp_path):
    source = FixtureSource()
    first = run_sync(tmp_path, source=source)
    original = {name: (tmp_path / name).read_bytes() for name in first["files"]}
    source.payloads["sanitation"][0]["unidade"] = "Pessoas"

    report = run_sync(tmp_path, source=source)

    assert report["status"] == "failed"
    assert report["cache_preserved"] is True
    assert report["last_successful_sync"] == first["finished_at"]
    assert report["files"] == []
    assert "unidade incompatível" in report["errors"][0]["message"]
    assert {name: (tmp_path / name).read_bytes() for name in original} == original


def test_optional_national_failure_with_previous_cache_keeps_last_good_data(tmp_path):
    source = FixtureSource()
    run_sync(tmp_path, source=source)
    original = (tmp_path / "population-national.json").read_bytes()
    source.failures.add("population-national")

    report = run_sync(tmp_path, source=source)

    assert report["status"] == "completed"
    assert [warning["job"] for warning in report["warnings"]] == ["population-national"]
    assert (tmp_path / "population-national.json").read_bytes() == original
    sources = {source["id"]: source for source in read(tmp_path, "sources.json")}
    assert sources["ibge-censo-populacao-nacional"]["last_synced"] == FETCHED_AT


def test_optional_national_failure_without_cache_is_unavailable(tmp_path):
    source = FixtureSource()
    source.failures.add("population-national")

    report = run_sync(tmp_path, source=source)

    assert report["status"] == "completed"
    assert not (tmp_path / "population-national.json").exists()
    assert (tmp_path / "catalog.json").is_file()
    sources = {source["id"]: source for source in read(tmp_path, "sources.json")}
    assert sources["ibge-censo-populacao-nacional"]["status"] == "unavailable"


@pytest.mark.parametrize("url", [
    "http://servicodados.ibge.gov.br/api",
    "https://servicodados.ibge.gov.br.example.com/api",
    "https://example.com@servicodados.ibge.gov.br/api",
])
def test_connector_rejects_unapproved_targets(url):
    with OfficialSource() as source, pytest.raises(ValueError, match="domínios"):
        source.fetch(url)
