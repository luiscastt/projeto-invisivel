"""Normalize public CKAN records from the government of Espírito Santo."""

from __future__ import annotations

from collections import Counter, defaultdict
import re
from unicodedata import combining, normalize


SCHOOLS_SOURCE_URL = (
    "https://dados.es.gov.br/dataset/informacoes-referentes-as-unidades-escolares-da-rede-estadual"
    "/resource/c7b1761f-0ca9-4384-a1f3-44a085cf9873"
)
OMBUDSMAN_YEAR = "2025"
OMBUDSMAN_SOURCE_URL = (
    "https://dados.es.gov.br/dataset/manifestacoes-da-ouvidoria"
    "/resource/edbe3888-9138-4174-b52f-52394ef025cb"
)
_MANIFESTATION_TYPES = (
    "Denúncia", "Elogio", "Informação", "Reclamação", "Solicitação", "Sugestão",
)
_MANIFESTATION_STATUSES = (
    "Arquivada", "Despachada", "Despacho Respondido", "Diligência",
    "Em Andamento", "Em Apuração", "Em tratamento", "Encerrada", "Encerrada Automaticamente",
)


def _key(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    unaccented = "".join(char for char in normalize("NFKD", value) if not combining(char))
    return " ".join(unaccented.casefold().split())


def _municipality_codes(catalog: dict) -> dict[str, str]:
    codes: dict[str, str] = {}
    for row in catalog["municipalities"]:
        if row["state_abbreviation"] != "ES":
            continue
        key = _key(row["name"])
        code = row["code"]
        if key in codes and codes[key] != code:
            raise ValueError("Municípios do Espírito Santo têm nomes ambíguos no catálogo")
        codes[key] = code
    return codes


def _school_point(row: dict) -> dict | None:
    try:
        latitude = float(str(row.get("latitude")).replace(",", "."))
        longitude = float(str(row.get("longitude")).replace(",", "."))
    except ValueError:
        return None
    # Broad bounds around Espírito Santo discard invalid placeholders and misplaced points.
    if -22 <= latitude <= -17 and -42 <= longitude <= -38:
        return {"type": "Point", "coordinates": [longitude, latitude]}
    return None


def normalize_schools(records: list[dict], catalog: dict) -> dict:
    """Build a GeoJSON collection for the state school network."""
    codes = _municipality_codes(catalog)
    schools = {}
    for row in records:
        municipality_code = codes.get(_key(row["nm_municipio"]))
        inep_id = str(row["inep_escola"]).strip()
        name = (row["nm_escola"] or "").strip()
        if not municipality_code or not re.fullmatch(r"32[0-9]{6}", inep_id) or not name:
            continue
        feature = {
            "type": "Feature",
            "id": inep_id,
            "properties": {
                "inep_id": inep_id,
                "name": name,
                "municipality_code": municipality_code,
                "network": "state",
                "source_name": "SEDU-ES",
                "source_url": SCHOOLS_SOURCE_URL,
            },
            "geometry": _school_point(row),
        }
        if inep_id in schools and schools[inep_id] != feature:
            raise ValueError(f"Cadastro estadual tem registros divergentes para a escola {inep_id}")
        schools[inep_id] = feature
    return {"type": "FeatureCollection", "features": [schools[key] for key in sorted(schools)]}


def _category(value: str | None, labels: dict[str, str]) -> str:
    key = _key(value)
    if not key:
        return "Não informado"
    return labels.get(key, "Outros")


def normalize_ombudsman(records: list[dict], catalog: dict) -> dict:
    """Aggregate 2025 records by the municipality declared in the dataset."""
    codes = _municipality_codes(catalog)
    types = {_key(label): label for label in _MANIFESTATION_TYPES}
    statuses = {_key(label): label for label in _MANIFESTATION_STATUSES}
    counts_by_type: dict[str, Counter[str]] = defaultdict(Counter)
    counts_by_status: dict[str, Counter[str]] = defaultdict(Counter)
    quality = {
        "accepted_rows": 0, "unmapped_rows": 0, "ignored_year_rows": 0, "total_rows": len(records),
    }
    for row in records:
        if str(row["Ano"]).strip() != OMBUDSMAN_YEAR:
            quality["ignored_year_rows"] += 1
            continue
        municipality_code = codes.get(_key(row["Municipio"]))
        if not municipality_code:
            quality["unmapped_rows"] += 1
            continue
        quality["accepted_rows"] += 1
        counts_by_type[municipality_code][_category(row["TipoManifestacao"], types)] += 1
        counts_by_status[municipality_code][_category(row["Situacao"], statuses)] += 1
    return {
        "year": OMBUDSMAN_YEAR,
        "quality": quality,
        "municipalities": {
            code: {
                "year": OMBUDSMAN_YEAR,
                "total": counts_by_type[code].total(),
                "by_type": dict(sorted(counts_by_type[code].items())),
                "by_status": dict(sorted(counts_by_status[code].items())),
            }
            for code in sorted(counts_by_type)
        },
    }
