"""Small official ES datasets: state schools and aggregated 2025 ombudsman records."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from .public_services import PublicAPI
from .espirito_santo import normalize_schools, normalize_ombudsman, SCHOOLS_SOURCE_URL, OMBUDSMAN_SOURCE_URL
from .sync import _atomic_json
from .connectors import utc_now

CKAN = "https://dados.es.gov.br/api/3/action/datastore_search"
SCHOOLS_ID = "c7b1761f-0ca9-4384-a1f3-44a085cf9873"
OMBUDSMAN_ID = "edbe3888-9138-4174-b52f-52394ef025cb"


def collect_records(resource, fetch):
    records = []
    seen = set()
    total = None
    for offset in range(0, 1000000, 1000):
        params = {"resource_id": resource, "limit": 1000, "offset": offset}
        if resource == OMBUDSMAN_ID:
            params["fields"] = "_id,Municipio,Ano,TipoManifestacao,Situacao"
        body = fetch(CKAN, params=params)
        if body.get("success") is not True:
            raise ValueError("CKAN não confirmou sucesso")
        data = body["result"]
        if total is not None and total != data["total"]:
            raise ValueError("Base mudou durante a paginação; tente novamente")
        total = data["total"]
        batch = data["records"]
        ids = [r["_id"] for r in batch]
        if seen.intersection(ids):
            raise ValueError("Paginação CKAN repetiu registros")
        seen.update(ids)
        records.extend(batch)
        if len(records) == total:
            return records
        if not batch or len(records) > total:
            raise ValueError("Paginação CKAN incompleta")
    raise ValueError("Limite de coleta CKAN excedido")


def sync_es(output=Path("data/official"), fetch=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
    live = PublicAPI() if fetch is None else None
    fetch = fetch or live
    manifest = {"fetched_at": utc_now(), "jobs": [], "errors": []}
    for name, resource, normalize, filename, source in [("sedu-schools", SCHOOLS_ID, normalize_schools, "schools-es.json", SCHOOLS_SOURCE_URL), ("ouvidoria-es", OMBUDSMAN_ID, normalize_ombudsman, "ombudsman-es.json", OMBUDSMAN_SOURCE_URL)]:
        try:
            records = collect_records(resource, fetch)
            result = normalize(records, catalog)
            if name == "ouvidoria-es":
                # Only allowlisted category counts leave this function. No protocols, sex, text or identities.
                result["source_url"] = source
                result["notes"] = "Ouvidoria estadual do ES, 2025. Município informado no registro; não representa localização de um problema de rua nem a base federal do Fala.BR. Registros sem município não são redistribuídos."
            result["fetched_at"] = utc_now()
            _atomic_json(output, filename, result)
            manifest["jobs"].append({"source": name, "status": "completed", "records": len(records), "source_url": source, "sha256": hashlib.sha256((output / filename).read_bytes()).hexdigest(), "quality": result.get("quality")})
        except Exception as exc:
            manifest["errors"].append({"source": name, "error_type": type(exc).__name__, "cache_preserved": (output / filename).exists()})
    if live:
        live.client.close()
    manifest["status"] = "partial" if manifest["errors"] else "completed"
    _atomic_json(output, "es-manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    args = parser.parse_args()
    result = sync_es(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["errors"] else 0)
