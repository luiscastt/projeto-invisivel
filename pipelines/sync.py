"""Download and publish the official territorial dataset for the MVP."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from uuid import uuid4

from .connectors import (
    MUNICIPALITIES_URL,
    NATIONAL_POPULATION_URL,
    NEIGHBORHOOD_LAYERS,
    PILOTS,
    POPULATION_URL,
    SANITATION_URL,
    STATES_URL,
    SURVEYS_URL,
    OfficialSource,
    aggregate_value,
    assert_sewer_series,
    boundary_center,
    boundary_url,
    make_catalog,
    neighborhoods_url,
    normalize_national_population,
    normalize_neighborhoods,
    survey_observation,
    utc_now,
)

MANIFEST_FILENAME = "ingestion-manifest.json"
NATIONAL_JOB = "population-national"
NATIONAL_FILE = "population-national.json"
NATIONAL_SOURCE_ID = "ibge-censo-populacao-nacional"
URLS = {
    "states": STATES_URL,
    "municipalities": MUNICIPALITIES_URL,
    "population": POPULATION_URL,
    NATIONAL_JOB: NATIONAL_POPULATION_URL,
    "surveys": SURVEYS_URL,
    "sanitation": SANITATION_URL,
    **{f"geometry-{code}": boundary_url(code) for code in PILOTS},
    **{f"neighborhoods-{code}": neighborhoods_url(code) for code in PILOTS},
}


def _atomic_json(output: Path, name: str, value) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output, prefix=f".{name}.", suffix=".tmp", mode="w",
            encoding="utf-8", newline="\n", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output / name)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _read_json(output: Path, name: str, default):
    try:
        return json.loads((output / name).read_bytes())
    except (OSError, ValueError):
        return default


def _indicator(
    identifier: str, name: str, sector: str, value: int | float | None, unit: str,
    year: str, source_name: str, source_url: str, fetched_at: str,
) -> dict:
    if value is None:
        raise ValueError(f"Valor ausente na origem para {identifier} em {year}")
    if value < 0 or unit == "%" and value > 100:
        raise ValueError(f"Valor fora do intervalo esperado para {identifier} em {year}")
    return {
        "id": identifier, "name": name, "sector": sector, "value": value,
        "unit": unit, "year": year, "source_name": source_name,
        "source_url": source_url, "granularity": "municipality",
        "quality": "official", "fetched_at": fetched_at,
    }


def _indicators(code: str, payloads: dict, fetched: dict) -> list[dict]:
    surveys = payloads["surveys"]
    estimated_year, estimated_value = survey_observation(surveys, 29171, code)
    mortality_year, mortality_value = survey_observation(surveys, 30279, code)
    school_year, school_value = survey_observation(surveys, 60045, code, "2022")
    specs = [
        (
            "population", "População residente no Censo", "demography",
            aggregate_value(payloads["population"], 93, code, "2022"), "pessoas", "2022",
            "IBGE · Censo Demográfico, SIDRA 4714", "population",
        ),
        (
            "population_estimate", "População estimada", "demography", estimated_value,
            "pessoas", estimated_year, "IBGE · Estimativas da População", "surveys",
        ),
        (
            "schooling", "Escolarização de 6 a 14 anos", "education", school_value, "%",
            school_year, "IBGE · Censo Demográfico", "surveys",
        ),
        (
            "infant_mortality", "Taxa de mortalidade infantil", "health", mortality_value,
            "óbitos por mil nascidos vivos", mortality_year, "DATASUS · IBGE Cidades", "surveys",
        ),
        (
            "sewage_network", "Domicílios com esgoto por rede geral, pluvial ou fossa ligada à rede",
            "sanitation", aggregate_value(payloads["sanitation"], 1000381, code, "2022"), "%",
            "2022", "IBGE · Censo Demográfico, SIDRA 6805", "sanitation",
        ),
    ]
    return [
        _indicator(identifier, name, sector, value, unit, year, source_name, URLS[key], fetched[key]["fetched_at"])
        for identifier, name, sector, value, unit, year, source_name, key in specs
    ]


def _source(
    identifier: str, name: str, organization: str, url: str, description: str,
    reference: str, granularity: str, notes: str, *, status: str = "active",
    records: int | None = None, synced: str | None = None,
) -> dict:
    return {
        "id": identifier, "name": name, "organization": organization, "url": url,
        "description": description, "status": status, "last_synced": synced,
        "reference": reference, "granularity": granularity, "records": records, "notes": notes,
    }


def _national_source(cache: dict, fetched: dict, output: Path) -> dict:
    if NATIONAL_FILE in cache:
        records = len(cache[NATIONAL_FILE])
        synced = fetched[NATIONAL_JOB]["fetched_at"]
        status = "active"
        notes = "Tabela SIDRA 4714. A cobertura corresponde à divisão municipal do Censo 2022."
    else:
        old_population = _read_json(output, NATIONAL_FILE, {})
        old_source = next(
            (row for row in _read_json(output, "sources.json", []) if row.get("id") == NATIONAL_SOURCE_ID),
            {},
        )
        records = len(old_population) if old_population else None
        synced = old_source.get("last_synced")
        status = "active" if old_population else "unavailable"
        notes = (
            "Falha na última atualização. Os registros disponíveis ainda são da última coleta válida."
            if old_population else "A série nacional está indisponível nesta versão do cache."
        )
    return _source(
        NATIONAL_SOURCE_ID, "Censo Demográfico · população nacional", "IBGE", NATIONAL_POPULATION_URL,
        "População residente municipal segundo o Censo Demográfico.", "2022", "municipality", notes,
        status=status, records=records, synced=synced,
    )


def _sources(cache: dict, fetched: dict, output: Path) -> list[dict]:
    return [
        _source(
            "ibge-localidades", "Localidades", "IBGE", STATES_URL,
            "Catálogo de estados e municípios.", "Catálogo vigente", "municipality",
            "O código de município tem sete dígitos.",
            records=len(cache["catalog.json"]["municipalities"]), synced=fetched["municipalities"]["fetched_at"],
        ),
        _source(
            "ibge-censo-populacao", "Censo Demográfico · população", "IBGE", POPULATION_URL,
            "População residente em Serra e Vitória.", "2022", "municipality",
            "Tabela SIDRA 4714, variável 93.", records=len(PILOTS), synced=fetched["population"]["fetched_at"],
        ),
        _national_source(cache, fetched, output),
        _source(
            "ibge-pesquisas", "Pesquisas e indicadores municipais", "IBGE / DATASUS", SURVEYS_URL,
            "Estimativa populacional, escolarização e mortalidade infantil.", "Séries anuais", "municipality",
            "O ano da observação é exibido com cada indicador.",
            records=3 * len(PILOTS), synced=fetched["surveys"]["fetched_at"],
        ),
        _source(
            "ibge-sidra-esgoto", "Censo Demográfico · esgotamento sanitário", "IBGE", SANITATION_URL,
            "Percentual de domicílios particulares permanentes ocupados com esgoto por rede geral, pluvial ou fossa ligada à rede.",
            "2022", "municipality", "Tabela SIDRA 6805, variável 1000381 e categoria 46290.",
            records=len(PILOTS), synced=fetched["sanitation"]["fetched_at"],
        ),
        _source(
            "ibge-malhas", "Malhas municipais", "IBGE", boundary_url(PILOTS[0]),
            "Polígonos municipais do piloto e ponto interno de referência no mapa.",
            "Malha vigente", "municipality", "Geometria em longitude e latitude.",
            records=len(PILOTS), synced=max(fetched[f"geometry-{code}"]["fetched_at"] for code in PILOTS),
        ),
        *[
            _source(
                f"bairros-{code}", f"Limites de bairros · {city}", f"Prefeitura de {city}", NEIGHBORHOOD_LAYERS[code],
                description, "Camada municipal", "neighborhood", notes,
                records=len(cache[f"neighborhoods-{code}.json"]),
                synced=fetched[f"neighborhoods-{code}"]["fetched_at"],
            )
            for code, city, description, notes in (
                ("3205002", "Serra", "Limites conforme Lei Municipal 4.514/2016.", "A camada inclui a Área Rural."),
                ("3205309", "Vitória", "Limites de bairros divulgados pelo GeoWeb.", "Camada 32 do serviço HubGeoweb."),
            )
        ],
        _source(
            "sinisa", "Sistema Nacional de Informações em Saneamento Básico", "Ministério das Cidades",
            "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025",
            "Planilhas de saneamento publicadas para download.", "2024", "municipality",
            "Importação das planilhas pendente de configuração.", status="requires_configuration",
        ),
        _source(
            "cnes", "Cadastro Nacional de Estabelecimentos de Saúde", "Ministério da Saúde",
            "https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude",
            "Cadastro de estabelecimentos de saúde.", "Catálogo vigente", "establishment",
            "Importação municipal pendente de verificação.", status="requires_configuration",
        ),
        _source(
            "obrasgov", "Obrasgov.br", "Ministério da Gestão e da Inovação em Serviços Públicos",
            "https://api-publica.obrasgov.gestao.gov.br/obras/docs",
            "Projetos de investimento em infraestrutura cadastrados na plataforma federal.",
            "API vigente", "project", "Importação municipal pendente de configuração.",
            status="requires_configuration",
        ),
        _source(
            "inep-censo-escolar", "Censo Escolar da Educação Básica", "INEP",
            "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar",
            "Microdados públicos anuais do Censo Escolar.", "2025", "school",
            "Arquivos públicos para download. A importação e a consolidação por município estão pendentes.",
            status="requires_configuration",
        ),
        _source(
            "portal-transparencia", "Portal da Transparência do Governo Federal", "CGU",
            "https://portaldatransparencia.gov.br/api-de-dados",
            "Consultas fiscais e administrativas do Executivo federal.", "Consulta conforme o conjunto", "dataset",
            "API requer chave da CGU no cabeçalho chave-api-dados. O escopo depende de cada conjunto de dados.",
            status="requires_configuration",
        ),
        _source(
            "fala-br", "Plataforma Integrada de Ouvidoria e Acesso à Informação", "CGU",
            "https://falabr.cgu.gov.br/help",
            "Serviços de consulta e tratamento de manifestações.", "Documentação da API", "manifestation",
            "OAuth 2.0 e permissões da organização para manifestações. O Painel Resolveu oferece dados públicos agregados.",
            status="requires_configuration",
        ),
    ]


def _build_snapshot(payloads: dict, fetched: dict) -> dict:
    assert_sewer_series(payloads["sanitation"])
    centers = {code: boundary_center(payloads[f"geometry-{code}"], code) for code in PILOTS}
    cache = {
        "catalog.json": make_catalog(payloads["states"], payloads["municipalities"], centers),
    }
    for code in PILOTS:
        cache[f"indicators-{code}.json"] = _indicators(code, payloads, fetched)
        cache[f"geometry-{code}.json"] = payloads[f"geometry-{code}"]
        layer = f"neighborhoods-{code}"
        cache[f"{layer}.json"] = normalize_neighborhoods(payloads[layer], code, URLS[layer])
    return cache


def run_sync(output: Path | str = Path("data/official"), *, source: OfficialSource | None = None) -> dict:
    """Return a manifest for this attempt, preserving the cache on upstream failures."""
    if source is None:
        with OfficialSource() as live_source:
            return run_sync(output, source=live_source)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    previous = _read_json(output, MANIFEST_FILENAME, {})
    last_successful_sync = previous.get("last_successful_sync")
    if not last_successful_sync and previous.get("status") == "completed":
        last_successful_sync = previous.get("finished_at")
    job_id = str(uuid4())
    started_at = utc_now()
    payloads: dict = {}
    fetched: dict = {}
    errors: list[dict] = []
    warnings: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(source.fetch, url): key for key, url in URLS.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                payloads[key], fetched[key] = future.result()
            except Exception as exc:
                problems = warnings if key == NATIONAL_JOB else errors
                problems.append({"job": key, "url": URLS[key], "message": str(exc)})
    written: list[str] = []
    if not errors:
        try:
            snapshot = _build_snapshot(payloads, fetched)
            if NATIONAL_JOB in payloads:
                try:
                    pilot_values = {
                        code: next(
                            indicator["value"] for indicator in snapshot[f"indicators-{code}.json"]
                            if indicator["id"] == "population"
                        )
                        for code in PILOTS
                    }
                    snapshot[NATIONAL_FILE] = normalize_national_population(payloads[NATIONAL_JOB], pilot_values)
                except (KeyError, ValueError, TypeError, AttributeError) as exc:
                    warnings.append({"job": NATIONAL_JOB, "url": URLS[NATIONAL_JOB], "message": str(exc)})
            snapshot["sources.json"] = _sources(snapshot, fetched, output)
            for name, value in snapshot.items():
                _atomic_json(output, name, value)
                written.append(name)
        except (KeyError, ValueError, TypeError, AttributeError, OSError) as exc:
            errors.append({"job": "publish", "url": None, "message": str(exc)})
    finished_at = utc_now()
    if not errors:
        last_successful_sync = finished_at
    manifest = {
        "id": job_id,
        "status": "failed" if errors else "completed",
        "started_at": started_at,
        "fetched_at": finished_at,
        "finished_at": finished_at,
        "last_successful_sync": last_successful_sync,
        "cache_preserved": bool(errors and not written and (output / "catalog.json").is_file()),
        "jobs": [
            {"job": key, "url": url, "status": "fetched" if key in fetched else "failed", **fetched.get(key, {})}
            for key, url in URLS.items()
        ],
        "errors": sorted(errors, key=lambda error: error["job"]),
        "warnings": warnings,
        "files": written,
    }
    _atomic_json(output, MANIFEST_FILENAME, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza o cache local de dados oficiais.")
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    arguments = parser.parse_args()
    manifest = run_sync(arguments.output)
    print(json.dumps(manifest, ensure_ascii=True, indent=2))
    return 1 if manifest["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
