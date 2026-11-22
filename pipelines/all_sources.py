"""Refresh public APIs without requiring the original local SINISA workbook."""
import json
from pathlib import Path
from dotenv import load_dotenv
from .sync import run_sync
from .public_services import sync_services
from .es_sync import sync_es
from .reported_problems import sync_reported_problems


def main():
    load_dotenv()
    output = Path("data/official")
    results = {"ibge": run_sync(output), "services": sync_services(output), "espirito_santo": sync_es(output)}
    try:
        results["reported_problems"] = sync_reported_problems(output / "reported-problems-es.json.gz")
    except Exception as exc:
        results["reported_problems"] = {"status": "failed", "errors": [{"source": "official_reported_problems", "error_type": type(exc).__name__, "cache_preserved": (output / "reported-problems-es.json.gz").exists()}]}
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if any(r.get("errors") for r in results.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
