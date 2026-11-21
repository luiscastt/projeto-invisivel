import json
import gzip
from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from .db import get_db
from .models import Issue, Report, Evidence

router = APIRouter(tags=["Territórios e dados oficiais"])


@lru_cache(maxsize=128)
def _read_snapshot(path: str, modified: int, size: int):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8-sig") as stream:
            return json.load(stream)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_file(request, name, default=None):
    path = request.app.state.settings.official_dir / name
    if not path.is_file() and (request.app.state.settings.official_dir / (name + ".gz")).is_file():
        path = request.app.state.settings.official_dir / (name + ".gz")
    if not path.is_file():
        return default
    try:
        stat = path.stat()
        return _read_snapshot(str(path), stat.st_mtime_ns, stat.st_size)
    except (ValueError, OSError):
        return default


def catalog(request):
    return load_file(request, "catalog.json", {"states": [], "municipalities": []})


def municipality(request, code):
    result = next((m for m in catalog(request)["municipalities"] if m["code"] == code), None)
    if result is None:
        raise HTTPException(404, "Município não encontrado. Sincronize o catálogo oficial do IBGE.")
    return result


def neighborhoods(request, code):
    municipality(request, code)
    return load_file(request, f"neighborhoods-{code}.json", [])


def indicators(request, code):
    municipality(request, code)
    values = [dict(v) for v in load_file(request, f"indicators-{code}.json", [])]
    national = load_file(request, "population-national.json", {})
    if not any(v["id"] == "population" for v in values) and code in national:
        src = next((s for s in load_file(request, "sources.json", []) if s["id"] == "ibge-censo-populacao-nacional"), {})
        values.append({"id": "population", "name": "População residente no Censo", "sector": "demography", "value": national[code], "unit": "pessoas", "year": "2022", "source_name": "IBGE · Censo Demográfico, SIDRA 4714", "source_url": "https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N6%5Ball%5D", "granularity": "municipality", "quality": "official", "fetched_at": src.get("last_synced")})
    sectors = [("population", "População residente", "demography", "pessoas"), ("schooling", "Escolarização de 6 a 14 anos", "education", "%"), ("infant_mortality", "Mortalidade infantil", "health", "óbitos por mil nascidos vivos"), ("sewage", "Esgotamento por rede ou fossa ligada à rede", "sanitation", "%")]
    existing = {v["sector"] for v in values}
    for id_, name, sector, unit in sectors:
        if sector not in existing:
            values.append({"id": id_, "name": name, "sector": sector, "value": None, "unit": unit, "year": None, "source_name": "IBGE", "source_url": "https://servicodados.ibge.gov.br/api/docs", "granularity": "municipality", "quality": "unavailable", "fetched_at": None})
    from .official_context import context_indicators
    return [*values, *context_indicators(request, code)]


def geometry(request, code):
    return load_file(request, f"geometry-{code}.json")


def validate_location(request, payload):
    m = municipality(request, payload.municipality_code)
    if m["state_code"] != payload.state_code:
        raise HTTPException(422, "O município não pertence ao estado informado.")
    choices = neighborhoods(request, payload.municipality_code)
    n = next((n for n in choices if n["name"] == payload.neighborhood), None)
    if payload.neighborhood and n is None:
        raise HTTPException(422, "Bairro não encontrado no catálogo deste município. Use a localização por ponto sem bairro.")
    geom = geometry(request, payload.municipality_code)
    if geom:
        try:
            polygon = unary_union([shape(f["geometry"]) for f in geom["features"]]) if geom.get("type") == "FeatureCollection" else shape(geom.get("geometry", geom))
            if not polygon.buffer(.0005).covers(Point(payload.longitude, payload.latitude)):
                raise HTTPException(422, "O ponto informado está fora dos limites oficiais do município.")
        except (ValueError, KeyError, TypeError):
            raise HTTPException(503, "Geometria oficial inválida. A localização não pôde ser validada.")
    if n and n.get("geometry"):
        if not shape(n["geometry"]).buffer(.0005).covers(Point(payload.longitude, payload.latitude)):
            raise HTTPException(422, "O ponto informado está fora do bairro selecionado.")


@router.get("/states")
def states(request: Request):
    return catalog(request)["states"]


@router.get("/states/{code}/municipalities")
def municipalities(code: str, request: Request):
    c = catalog(request)
    if not any(s["code"] == code for s in c["states"]):
        raise HTTPException(404, "Estado não encontrado.")
    return [m for m in c["municipalities"] if m["state_code"] == code]


@router.get("/municipalities/{code}/neighborhoods")
def list_neighborhoods(code: str, request: Request):
    return [{k: v for k, v in n.items() if k != "geometry"} for n in neighborhoods(request, code)]


@router.get("/territories/{code}/geometry")
def get_geometry(code: str, request: Request):
    municipality(request, code)
    g = geometry(request, code)
    if g is None:
        raise HTTPException(404, "Limite territorial ainda não disponível no cache oficial.")
    return g


@router.get("/territories/{code}/neighborhood-geometries")
def neighborhood_geometries(code: str, request: Request):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"id": n["id"], "name": n["name"]}, "geometry": n["geometry"]} for n in neighborhoods(request, code) if n.get("geometry")]}


@router.get("/territories/{code}/indicators")
def get_indicators(code: str, request: Request):
    return indicators(request, code)


@router.get("/territories/{code}/summary")
def summary(code: str, request: Request, demo: bool = False, db: Session = Depends(get_db, scope="function")):
    m = municipality(request, code)
    filters = [Issue.municipality_code == code, Issue.is_demo == demo, Issue.merged_into.is_(None)]
    count = db.scalar(select(func.count()).select_from(Issue).where(*filters)) or 0
    resolved = db.scalar(select(func.count()).select_from(Issue).where(*filters, Issue.operational_status == "verified_resolved")) or 0
    issue_ids = select(Issue.id).where(*filters)
    return {"municipality": m, "counts": {"total": count, "unresolved": count - resolved, "resolved": resolved, "reports": db.scalar(select(func.count()).select_from(Report).where(Report.issue_id.in_(issue_ids), Report.moderation_status == "approved")) or 0, "evidence": db.scalar(select(func.count()).select_from(Evidence).where(Evidence.issue_id.in_(issue_ids), Evidence.approved == True)) or 0}, "indicators": indicators(request, code), "coverage": {"neighborhoods": len(neighborhoods(request, code)), "boundaries_available": geometry(request, code) is not None}, "assessment": {"score": None, "reason": "Sem avaliação composta: indicadores de períodos e metodologias diferentes não são somados. Ausência de relatos não significa ausência de problemas."}}


@router.get("/sources")
def sources(request: Request):
    result = [dict(v) for v in load_file(request, "sources.json", [])]
    manifest = load_file(request, "ingestion-manifest.json", {})
    if manifest.get("status") in ("failed", "partial"):
        for s in result:
            if s["status"] == "active":
                s["stale"] = True
                s["notes"] += " A última tentativa de sincronização teve falhas. Este é o último cache válido; consulte a data da coleta."
    from .official_context import augment_sources
    return augment_sources(request, result)
