"""Verified public-service APIs. Responses are context, never citizen issue reports."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from dotenv import load_dotenv
from .connectors import utc_now, PILOTS
from .sync import _atomic_json

CNES = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
OBRAS = "https://api-publica.obrasgov.gestao.gov.br/obras"
PORTAL = "https://api.portaldatransparencia.gov.br/api-de-dados/convenios"
ALLOWED = {"apidadosabertos.saude.gov.br", "api-publica.obrasgov.gestao.gov.br", "api.portaldatransparencia.gov.br", "dados.es.gov.br"}


def number(value):
    if value in (None, "", "-", "...", "Não informado"):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Número não finito na origem")
    return result


def coordinates(lat, lng):
    try:
        lat, lng = number(lat), number(lng)
        if lat is not None and lng is not None and -34 <= lat <= 6 and -74 <= lng <= -28:
            return lat, lng
    except (ValueError, TypeError):
        pass
    return None, None


def normalize_cnes(rows, code):
    result, seen = [], set()
    for row in rows:
        if str(row.get("codigo_municipio")) != code[:6]:
            raise ValueError("CNES retornou estabelecimento de outro município")
        id_ = str(row["codigo_cnes"]).zfill(7)
        if id_ in seen:
            raise ValueError("CNES repetido na paginação")
        seen.add(id_)
        lat, lng = coordinates(row.get("latitude_estabelecimento_decimo_grau"), row.get("longitude_estabelecimento_decimo_grau"))
        if code.startswith("32") and lat is not None and not (-22 <= lat <= -17 and -42 <= lng <= -38):
            lat, lng = None, None
        sus = str(row.get("estabelecimento_faz_atendimento_ambulatorial_sus", "")).strip().upper()
        result.append({"id": id_, "municipality_code": code, "name": row.get("nome_fantasia") or "Estabelecimento sem nome fantasia", "category": "health", "latitude": lat, "longitude": lng, "neighborhood": row.get("bairro_estabelecimento"), "unit_type": row.get("codigo_tipo_unidade"), "attends_sus": True if sus == "SIM" else False if sus in ("NAO", "NÃO") else None, "updated_at": row.get("data_atualizacao"), "source_url": f"https://cnes.datasus.gov.br/pages/estabelecimentos/ficha/identificacao/{code[:6]}{id_}"})
    return sorted(result, key=lambda x: x["id"])


def collect_cnes(code, fetch):
    rows, seen = [], set()
    for page in range(500):
        body = fetch(CNES, params={"codigo_municipio": code[:6], "status": 1, "limit": 20, "offset": page})
        batch = body.get("estabelecimentos") if isinstance(body, dict) else None
        if not isinstance(batch, list):
            raise ValueError("Resposta CNES incompatível")
        if not batch:
            return rows
        ids = [str(r["codigo_cnes"]) for r in batch]
        if seen.intersection(ids):
            raise ValueError("Paginação CNES repetida; cache anterior preservado")
        rows.extend(batch)
        seen.update(ids)
    raise ValueError("Limite de paginação CNES excedido; resposta não tratada como completa")


def normalize_works(projects, code):
    result = []
    for p in projects:
        id_ = str(p["id_projeto_investimento"])
        pins = [coordinates(pin.get("latitude"), pin.get("longitude")) for pin in p.get("pins", [])]
        lat, lng = next((point for point in pins if point[0] is not None), (None, None))
        if code.startswith("32") and lat is not None and not (-22 <= lat <= -17 and -42 <= lng <= -38):
            lat, lng = None, None
        values = [number(i.get("vl_investimento_previsto")) for i in p.get("investimentos_previstos", [])]
        values = [v for v in values if v is not None]
        types = " ".join(str(i.get("tipo", "")) for i in p.get("eixos_tipos", [])).casefold()
        category = "health" if "saúde" in types else "education" if "educa" in types else "sanitation" if "sanea" in types else "mobility" if "mobil" in types or "transporte" in types else "infrastructure"
        result.append({"id": id_, "municipality_code": code, "name": p.get("desc_nome") or p.get("desc_projeto") or id_, "description": p.get("desc_projeto"), "status": p.get("situacao"), "category": category, "latitude": lat, "longitude": lng, "planned_investment": sum(values) if values else None, "organization": p.get("organizacao_resp"), "reference_year": str(p["ano_cadastro"]) if p.get("ano_cadastro") else None, "planned_start": p.get("dt_inicial_prevista"), "planned_end": p.get("dt_final_prevista"), "source_url": f"https://api-publica.obrasgov.gestao.gov.br/obras/projeto-investimento?id_projeto_investimento={id_}"})
    return sorted(result, key=lambda x: x["id"])


def _obras_pages(fetch, endpoint, params):
    rows = []
    for page in range(1, 1001):
        body = fetch(f"{OBRAS}/{endpoint}", params={**params, "pagina": page, "tamanho_da_pagina": 200})
        if not isinstance(body.get("data"), list):
            raise ValueError("Resposta Obrasgov incompatível")
        rows.extend(body["data"])
        if page >= int(body["total_pages"]):
            if len(rows) != int(body["total_items"]):
                raise ValueError("Paginação Obrasgov incompleta")
            return rows
    raise ValueError("Limite de paginação Obrasgov excedido")


def collect_works(code, fetch):
    geometries = _obras_pages(fetch, "geometria", {"cod_ibge": code})
    if any(str(g.get("cod_ibge")) != code for g in geometries):
        raise ValueError("Obrasgov retornou geometria de outro município")
    ids = sorted({g["id_projeto_investimento"] for g in geometries})
    def project(id_):
        rows = _obras_pages(fetch, "projeto-investimento", {"id_projeto_investimento": id_})
        if len(rows) != 1 or rows[0]["id_projeto_investimento"] != id_:
            raise ValueError("Projeto Obrasgov não corresponde à geometria")
        return rows[0]
    with ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(project, ids))


def normalize_funding(rows, code):
    result = []
    for p in rows:
        if str(p.get("municipioConvenente", {}).get("codigoIBGE")) != code:
            raise ValueError("Transparência retornou convênio de outro município")
        d = p.get("dimConvenio") or {}
        reference = p.get("dataReferencia")
        result.append({"id": str(p["id"]), "municipality_code": code, "name": d.get("objeto") or "Convênio federal", "number": d.get("numero"), "status": p.get("situacao"), "amount": number(p.get("valor")), "released": number(p.get("valorLiberado")), "start": p.get("dataInicioVigencia"), "end": p.get("dataFinalVigencia"), "reference_date": None if reference == "1900-01-01" else reference, "organization": (p.get("orgao") or {}).get("nome"), "source_url": f"https://portaldatransparencia.gov.br/convenios/{p['id']}"})
    return sorted(result, key=lambda x: (x.get("start") or "", x["id"]), reverse=True)


def collect_funding(code, fetch, key):
    rows, seen = [], set()
    for page in range(1, 501):
        batch = fetch(PORTAL, params={"codigoIBGE": code, "dataVigenciaInicial": "01/01/2020", "dataVigenciaFinal": "31/12/2030", "pagina": page}, headers={"chave-api-dados": key})
        if not isinstance(batch, list):
            raise ValueError("Resposta de convênios incompatível")
        if not batch:
            return rows
        ids = [str(r["id"]) for r in batch]
        if seen.intersection(ids):
            raise ValueError("Paginação de convênios repetida")
        seen.update(ids)
        rows.extend(batch)
        time.sleep(.12)
    raise ValueError("Limite de paginação de convênios excedido")


class PublicAPI:
    def __init__(self):
        self.client = httpx.Client(timeout=35, follow_redirects=False, headers={"User-Agent": "INVISIVEL/0.2 public-data-ingestion"})

    def __call__(self, url, params=None, headers=None):
        if urlsplit(url).scheme != "https" or urlsplit(url).hostname not in ALLOWED:
            raise ValueError("Origem pública não autorizada")
        for attempt in range(3):
            try:
                r = self.client.get(url, params=params, headers=headers)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
            except (httpx.TransportError, ValueError):
                if attempt == 2:
                    raise
            time.sleep(1 + attempt * 2)


def sync_services(output, codes=PILOTS, fetch=None, transparency_key=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    live = PublicAPI() if fetch is None else None
    fetch = fetch or live
    key = transparency_key or os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
    manifest = {"fetched_at": utc_now(), "jobs": [], "errors": []}
    try:
        for code in codes:
            tasks = [("cnes", lambda: normalize_cnes(collect_cnes(code, fetch), code), CNES, "Cadastros ativos de estabelecimentos; inclui rede privada. Não comprova disponibilidade de atendimento."), ("obrasgov", lambda: normalize_works(collect_works(code, fetch), code), f"{OBRAS}/geometria?cod_ibge={code}", "Projetos com geometria vinculada ao município; cobertura federal não é inventário completo de obras municipais.")]
            if key:
                tasks.append(("transparencia", lambda: normalize_funding(collect_funding(code, fetch, key), code), PORTAL, "Convênios com filtro de vigência da API entre 01/01/2020 e 31/12/2030. Valores previstos e liberados não equivalem a custo de reparar problemas."))
            else:
                manifest["jobs"].append({"source":"transparencia","municipality_code":code,"status":"requires_configuration","cache_preserved":(output/f'transparencia-{code}.json').exists(),"notes":"Chave de API não configurada; nenhuma atualização desta fonte foi realizada."})
            for name, collect, url, notes in tasks:
                path = output / f"{name}-{code}.json"
                try:
                    items = collect()
                    payload = {"municipality_code": code, "items": items, "total": len(items), "complete": True, "fetched_at": utc_now(), "source_url": url, "notes": notes}
                    _atomic_json(output, path.name, payload)
                    manifest["jobs"].append({"source": name, "municipality_code": code, "status": "completed", "records": len(items), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                except Exception as e:
                    # Exception text/headers are never logged; API credentials cannot enter snapshots.
                    status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
                    manifest["errors"].append({"source": name, "municipality_code": code, "status_code": status, "error_type": type(e).__name__, "cache_preserved": path.exists()})
        manifest["status"] = "partial" if manifest["errors"] else "completed"
        _atomic_json(output, "services-manifest.json", manifest)
        return manifest
    finally:
        if live:
            live.client.close()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Sincroniza CNES, Obrasgov e convênios federais.")
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    args = parser.parse_args()
    result = sync_services(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
