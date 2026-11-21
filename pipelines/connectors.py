"""Fetch and normalize the public datasets used by the territorial directory."""

from __future__ import annotations

import hashlib
import math
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx
from shapely.geometry import shape
from shapely.validation import make_valid

IBGE = "https://servicodados.ibge.gov.br/api"
PILOTS = ("3205002", "3205309")
PILOT_LOCALITIES = "N6%5B3205002,3205309%5D"
STATES_URL = f"{IBGE}/v1/localidades/estados?orderBy=nome"
MUNICIPALITIES_URL = f"{IBGE}/v1/localidades/municipios?orderBy=nome"
SURVEYS_URL = (
    f"{IBGE}/v1/pesquisas/-/indicadores/29171%7C30279%7C60045/resultados/3205002%7C3205309"
)
POPULATION_URL = f"{IBGE}/v3/agregados/4714/periodos/2022/variaveis/93?localidades={PILOT_LOCALITIES}"
NATIONAL_POPULATION_URL = f"{IBGE}/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N6%5Ball%5D"
SANITATION_URL = (
    f"{IBGE}/v3/agregados/6805/periodos/2022/variaveis/1000381"
    f"?localidades={PILOT_LOCALITIES}&classificacao=11558%5B46290%5D"
)
NEIGHBORHOOD_LAYERS = {
    "3205002": "https://mapas.serra.es.gov.br/server/rest/services/Hosted/PLA_Bairro/FeatureServer/0",
    "3205309": "https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/32",
}
NEIGHBORHOOD_FIELDS = {
    "3205002": "objectid,pk_bairro_ctm,tx_bairro",
    "3205309": "OBJECTID,codBairro,nome",
}
PUBLIC_HOSTS = frozenset({
    "servicodados.ibge.gov.br", "mapas.serra.es.gov.br", "gis.vitoria.es.gov.br",
})


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def boundary_url(code: str) -> str:
    return f"{IBGE}/v3/malhas/municipios/{code}?formato=application%2Fvnd.geo%2Bjson&qualidade=maxima"


def neighborhoods_url(code: str) -> str:
    return (
        f"{NEIGHBORHOOD_LAYERS[code]}/query?where=1%3D1"
        f"&outFields={NEIGHBORHOOD_FIELDS[code]}&outSR=4326&f=geojson"
    )


class OfficialSource:
    def __init__(self, timeout: float = 25.0, attempts: int = 3):
        self.attempts = attempts
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=min(8.0, timeout)),
            follow_redirects=False,
            headers={
                "Accept": "application/json, application/geo+json, application/vnd.geo+json",
                "User-Agent": "Projeto-Invisivel/0.1 (public territorial data ingestion)",
            },
        )

    def __enter__(self) -> OfficialSource:
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def fetch(self, url: str) -> tuple[object, dict]:
        target = urlsplit(url)
        if (
            target.scheme != "https" or target.hostname not in PUBLIC_HOSTS
            or target.username or target.password or target.port not in (None, 443)
        ):
            raise ValueError("URL fora dos domínios públicos cadastrados")
        error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and "error" in payload:
                    raise ValueError("O servidor ArcGIS retornou um erro")
                return payload, {
                    "url": url,
                    "fetched_at": utc_now(),
                    "sha256": hashlib.sha256(response.content).hexdigest(),
                    "bytes": len(response.content),
                }
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code not in {429, 500, 502, 503, 504}:
                    raise
                error = exc
            except (httpx.TransportError, ValueError) as exc:
                error = exc
            if attempt + 1 < self.attempts:
                time.sleep(0.4 * (2 ** attempt))
        raise RuntimeError(f"Falha após {self.attempts} tentativas: {error}") from error


def make_catalog(states: list, municipalities: list, centers: dict[str, list[float]]) -> dict:
    state_records = [
        {"code": str(state["id"]), "name": state["nome"], "abbreviation": state["sigla"]}
        for state in states
    ]
    known_states = {state["code"]: state for state in state_records}
    records = []
    for row in municipalities:
        code = str(row["id"])
        state = known_states[code[:2]]
        records.append({
            "code": code,
            "name": row["nome"],
            "state_code": state["code"],
            "state_abbreviation": state["abbreviation"],
            "center": centers.get(code),
        })
    codes = {record["code"] for record in records}
    if (
        len(known_states) != 27 or len(state_records) != 27 or len(codes) < 5_500
        or len(codes) != len(records) or not set(PILOTS).issubset(codes)
        or any(len(code) != 7 or not code.isdecimal() for code in codes)
        or any(not record["name"] for record in records + state_records)
    ):
        raise ValueError("Catálogo nacional incompleto ou incompatível")
    return {"states": state_records, "municipalities": records}


def _number(raw) -> int | float | None:
    if raw in (None, "", "-", "...", "..", "X"):
        return None
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError("O indicador retornou um número não finito")
    return int(value) if value.is_integer() else value


def aggregate_value(rows: list, variable: int, municipality: str, period: str) -> int | float | None:
    matches = [
        row["serie"].get(period)
        for table in rows if str(table["id"]) == str(variable)
        for result in table["resultados"]
        for row in result["series"] if row["localidade"]["id"] == municipality
    ]
    if len(matches) != 1:
        raise ValueError(f"Série incompatível para o indicador {variable} e município {municipality}")
    return _number(matches[0])


def normalize_national_population(rows: list, pilot_values: dict[str, int]) -> dict[str, int]:
    if len(rows) != 1 or str(rows[0]["id"]) != "93" or rows[0]["unidade"].casefold() != "pessoas":
        raise ValueError("Série nacional de população incompatível com o Censo de 2022")
    series = [row for result in rows[0]["resultados"] for row in result["series"]]
    population: dict[str, int] = {}
    seen: set[str] = set()
    for row in series:
        code = str(row["localidade"]["id"])
        if len(code) != 7 or not code.isdecimal() or code in seen:
            raise ValueError("Série nacional de população trouxe códigos municipais inválidos ou duplicados")
        seen.add(code)
        value = _number(row["serie"].get("2022"))
        if value is None:
            continue
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"População censitária inválida para o município {code}")
        population[code] = value
    if len(population) < 5_500 or any(population.get(code) != value for code, value in pilot_values.items()):
        raise ValueError("Série nacional de população incompleta ou divergente dos recortes do piloto")
    return population


def survey_value(rows: list, indicator: int, municipality: str, period: str | None = None) -> int | float | None:
    return survey_observation(rows, indicator, municipality, period)[1]


def survey_observation(rows: list, indicator: int, municipality: str, period: str | None = None) -> tuple[str, int | float | None]:
    matches = [
        line["res"]
        for row in rows if row["id"] == indicator
        for line in row["res"] if line["localidade"] in (municipality, municipality[:6])
    ]
    if len(matches) != 1:
        raise ValueError(f"Série incompatível para o indicador {indicator} e município {municipality}")
    period = period or max((key for key in matches[0] if len(key) == 4 and key.isdecimal()), default="")
    if not period or period not in matches[0]:
        raise ValueError(f"Período incompatível para o indicador {indicator} e município {municipality}")
    return period, _number(matches[0][period])


def _polygon(geometry: dict):
    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("A geometria oficial precisa ser um polígono ou multipolígono")
    polygon = shape(geometry)
    if not polygon.is_valid:
        polygon = make_valid(polygon)
    if polygon.is_empty or not polygon.area > 0:
        raise ValueError("A geometria oficial está vazia")
    min_x, min_y, max_x, max_y = polygon.bounds
    if not (-180 <= min_x <= max_x <= 180 and -90 <= min_y <= max_y <= 90):
        raise ValueError("A geometria oficial não usa longitude e latitude")
    return polygon


def boundary_center(payload: dict, code: str) -> list[float]:
    features = payload["features"] if payload.get("type") == "FeatureCollection" else [payload]
    if len(features) != 1 or features[0].get("type") != "Feature":
        raise ValueError("A malha consultada não representa um único município")
    feature = features[0]
    published_code = feature.get("properties", {}).get("codarea")
    if published_code is not None and str(published_code) != code:
        raise ValueError(f"A malha consultada não pertence ao município {code}")
    point = _polygon(feature["geometry"]).representative_point()
    return [round(point.x, 6), round(point.y, 6)]


def normalize_neighborhoods(payload: dict, code: str, url: str) -> list[dict]:
    if (
        payload.get("type") != "FeatureCollection"
        or payload.get("exceededTransferLimit")
        or (payload.get("properties") or {}).get("exceededTransferLimit")
    ):
        raise ValueError("A consulta de bairros retornou uma camada incompleta")
    rows = []
    for feature in payload["features"]:
        properties = feature["properties"]
        if code == "3205002":
            local_id = properties["pk_bairro_ctm"]
            name = properties["tx_bairro"]
            if local_id is None:
                local_id = f"obj-{properties['objectid']}"
        else:
            local_id = properties["codBairro"]
            name = properties["nome"]
        if not isinstance(name, str) or not name.strip() or local_id is None:
            raise ValueError("A camada de bairros retornou uma identificação ausente")
        _polygon(feature["geometry"])
        rows.append({
            "id": f"{code}-{local_id}",
            "name": name.strip(),
            "geometry_status": "official",
            "source_url": url,
            "geometry": feature["geometry"],
        })
    if len(rows) < 2 or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("A camada de bairros está vazia ou tem chaves duplicadas")
    return sorted(rows, key=lambda row: row["name"].casefold())


def assert_sewer_series(payload: list) -> None:
    matches = [row for row in payload if str(row["id"]) == "1000381"]
    if len(matches) != 1:
        raise ValueError("A resposta de esgotamento sanitário deve conter a variável 1000381")
    unit = matches[0]["unidade"]
    if unit.strip().casefold() not in {"%", "percentual", "por cento"}:
        raise ValueError(f"A variável de esgotamento sanitário tem unidade incompatível: {unit!r}")
    for result in matches[0]["resultados"]:
        classifications = result["classificacoes"]
        if len(classifications) != 1:
            raise ValueError("A variável de esgotamento sanitário exige uma categoria")
        classification = classifications[0]
        if (
            str(classification["id"]) != "11558"
            or set(classification["categoria"]) != {"46290"}
        ):
            raise ValueError("A consulta de esgotamento sanitário trouxe a categoria errada")
