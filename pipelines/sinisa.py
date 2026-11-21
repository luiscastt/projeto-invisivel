"""Import the 2024 SINISA municipal management workbook (reference year 2023)."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import tempfile
from io import BytesIO, TextIOWrapper
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from .connectors import utc_now
from .sync import _atomic_json

SOURCE_ID = "sinisa-gestao-municipal-2024"
SOURCE_NAME = "SINISA 2024 · Gestão Municipal"
SOURCE_URL = (
    "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/"
    "saneamento/sinisa/resultados-sinisa/resultados-sinisa"
)
GLOSSARY_URL = (
    "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/"
    "saneamento/sinisa/area-do-prestador/arquivos/"
    "GLOSSARIO_INFORMACOES_SINISA_GESTAO_MUNICIPAL.pdf"
)
EDITION = "2024"
REFERENCE_YEAR = "2023"
MUNICIPALITIES_FILENAME = "sinisa-municipalities.json"
COMPRESSED_MUNICIPALITIES_FILENAME = f"{MUNICIPALITIES_FILENAME}.gz"
MANIFEST_FILENAME = "sinisa-manifest.json"

SHEET_NAME = "GM"
CODES_ROW = 11
LABELS_ROW = 12
UNITS_ROW = 13
DATA_ROW = 15
RESPONSE_COLUMN_LABEL = "Respondeu ao Módulo Gestão Municipal do SINISA 2024"
RESPONSE_VALUES = {"Sim": True, "Não": False}

CODED_COLUMNS = {
    "OGM3001": "BY",  # Municipal sanitation policy law
    "OGM3004": "CC",  # Municipal or regional sanitation plan
    "OGM3005": "CD",  # Type of approval instrument
    "OGM3006": "CE",  # Identifier of approval instrument
    "OGM3007": "CF",  # Promulgation date
    "OGM3008": "CG",  # Plan components
    "OGM3010": "CI",  # Plan areas
    "OGM3013": "CL",  # Municipal solid-waste plan
    "OGM3201": "DD",  # Municipal sanitation council
    "OGM1001": "BI",  # Reported existence of a public water distribution network service
    "OGM1101": "BK",  # Reported existence of a public sewer collection network service
    "OGM2001": "BQ",  # Water regulator
    "OGM2101": "BS",  # Sewer regulator
    "OGM4204": "AM",  # Municipality's total investment in water supply
    "OGM4304": "AZ",  # Municipality's total investment in sewerage
}
COUNT_COLUMNS = {
    "water-provider-count": ("BJ", "Quantidade de prestadores de Abastecimento de Água atuando no município"),
    "sewer-provider-count": ("BL", "Quantidade de prestadores de Esgoto atuando no município"),
}
MONEY_FIELDS = frozenset({"OGM4204", "OGM4304"})
YES_NO_FIELDS = frozenset({
    "OGM1001", "OGM1101", "OGM2001", "OGM2101", "OGM3001", "OGM3004", "OGM3013", "OGM3201",
})
EXPECTED_UNITS = dict.fromkeys(MONEY_FIELDS, "(R$/ano)") | dict.fromkeys(YES_NO_FIELDS, "(sim/não)")
BR_CURRENCY = re.compile(r"-?(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+),[0-9]{2}")
IBGE_CODE = re.compile(r"[1-5][0-9]{6}")


def _fields(codes: tuple, labels: tuple, units: tuple) -> dict[str, dict]:
    fields = {}
    for code, column in CODED_COLUMNS.items():
        index = column_index_from_string(column) - 1
        source_code = str(codes[index]).strip()
        label = labels[index]
        if source_code.rstrip("*").strip() != code or not isinstance(label, str) or not label.strip():
            raise ValueError(f"Cabeçalho incompatível com {code} na coluna {column}")
        unit = units[index]
        if code in EXPECTED_UNITS and unit != EXPECTED_UNITS[code]:
            raise ValueError(f"Unidade incompatível com {code} na coluna {column}")
        fields[code] = {"column": column, "label": label.strip(), "source_code": source_code}
        if isinstance(unit, str) and unit.strip():
            fields[code]["unit"] = unit.strip().removeprefix("(").removesuffix(")")
    for code, (column, label) in COUNT_COLUMNS.items():
        if codes[column_index_from_string(column) - 1] != label:
            raise ValueError(f"Cabeçalho de contagem incompatível na coluna {column}")
        fields[code] = {"column": column, "label": label, "source_code": None, "unit": "prestadores"}
    return fields


def _observation(raw, code: str, cell: str) -> tuple[str | int | float | None, str | None]:
    value = raw.strip() if isinstance(raw, str) else raw
    if value is None or value == "":
        return None, "blank"
    if value == "null":
        return None, "nonrespondent"
    if code in MONEY_FIELDS and isinstance(value, str) and BR_CURRENCY.fullmatch(value):
        value = float(value.replace(".", "").replace(",", "."))
    if code in MONEY_FIELDS and (type(value) not in (float, int) or not math.isfinite(value)):
        raise ValueError(f"Valor de investimento incompatível em {SHEET_NAME}!{cell}")
    if code in COUNT_COLUMNS and (type(value) is not int or value < 0):
        raise ValueError(f"Contagem incompatível em {SHEET_NAME}!{cell}")
    if code in YES_NO_FIELDS and value not in RESPONSE_VALUES:
        raise ValueError(f"Declaração incompatível em {SHEET_NAME}!{cell}")
    return value, None


def _indicator(code: str, field: dict, value: int | float | None, imported_at: str) -> dict:
    return {
        "id": f"sinisa-gm-{code.lower()}",
        "name": field["label"],
        "sector": "sanitation",
        "value": value,
        "unit": field["unit"],
        "year": REFERENCE_YEAR,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "granularity": "municipality",
        "quality": "official" if value is not None else "unavailable",
        "fetched_at": imported_at,
    }


def _municipalities(sheet, fields: dict, imported_at: str) -> dict[str, dict]:
    column_indexes = {
        code: column_index_from_string(field["column"]) - 1 for code, field in fields.items()
    }
    records = {}
    for row_number, row in enumerate(
        sheet.iter_rows(min_row=DATA_ROW, max_col=max(column_indexes.values()) + 1, values_only=True), DATA_ROW,
    ):
        if all(value is None for value in row):
            continue
        response, raw_code, name, state = row[:4]
        code = str(raw_code).strip()
        if not IBGE_CODE.fullmatch(code):
            raise ValueError(f"Código IBGE incompatível em {SHEET_NAME}!B{row_number}: {raw_code!r}")
        if code in records:
            raise ValueError(f"Código IBGE duplicado: {code} em {SHEET_NAME}!B{row_number}")
        if response not in RESPONSE_VALUES or not isinstance(name, str) or not isinstance(state, str):
            raise ValueError(f"Identificação municipal incompleta em {SHEET_NAME}!A{row_number}:D{row_number}")
        information = []
        indicators = []
        for field_code, field in fields.items():
            cell = f"{field['column']}{row_number}"
            value, missing_reason = _observation(row[column_indexes[field_code]], field_code, cell)
            info = {"code": field_code, "label": field["label"], "value": value}
            if "unit" in field:
                info["unit"] = field["unit"]
            if missing_reason:
                info["missing_reason"] = missing_reason
            information.append(info)
            if field_code in MONEY_FIELDS or field_code in COUNT_COLUMNS:
                indicators.append(_indicator(field_code, field, value, imported_at))
        records[code] = {
            "municipality_code": code,
            "municipality_name": name.strip(),
            "state_abbreviation": state.strip(),
            "reference_year": REFERENCE_YEAR,
            "responded": RESPONSE_VALUES[response],
            "information": information,
            "indicators": indicators,
            "source": {"id": SOURCE_ID, "name": SOURCE_NAME, "url": SOURCE_URL, "sheet": SHEET_NAME, "row": row_number},
        }
    if not records:
        raise ValueError("A planilha não contém registros municipais")
    return dict(sorted(records.items()))


def _write_compressed(output: Path, records: dict) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output, prefix=".sinisa-municipalities.", suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            with TextIOWrapper(
                gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0),
                encoding="utf-8", newline="\n",
            ) as content:
                json.dump(records, content, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                content.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output / COMPRESSED_MUNICIPALITIES_FILENAME)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def import_sinisa(path: Path, output: Path, *, compress: bool = False) -> dict:
    """Read the original XLSX and publish a municipal lookup and import manifest."""
    input_bytes = path.read_bytes()
    imported_at = utc_now()
    workbook = load_workbook(BytesIO(input_bytes), read_only=True, data_only=True, keep_links=False)
    try:
        if SHEET_NAME not in workbook.sheetnames:
            raise ValueError(f"A planilha precisa conter a aba {SHEET_NAME}")
        sheet = workbook[SHEET_NAME]
        if sheet["C3"].value != f"Diagnóstico de Gestão Municipal - {EDITION}":
            raise ValueError(f"A planilha precisa ser do módulo Gestão Municipal, edição {EDITION}")
        codes, labels, units = sheet.iter_rows(
            min_row=CODES_ROW, max_row=UNITS_ROW, max_col=column_index_from_string("DD"), values_only=True,
        )
        if codes[:4] != (RESPONSE_COLUMN_LABEL, "Cod_IBGE", "Município", "UF"):
            raise ValueError(f"Cabeçalho municipal incompatível em {SHEET_NAME}!A{CODES_ROW}:D{CODES_ROW}")
        fields = _fields(codes, labels, units)
        records = _municipalities(sheet, fields, imported_at)
        ignored_sheets = [name for name in workbook.sheetnames if name != SHEET_NAME]
    finally:
        workbook.close()

    respondent_count = sum(record["responded"] for record in records.values())
    manifest = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "glossary_url": GLOSSARY_URL,
        "edition": EDITION,
        "reference_year": REFERENCE_YEAR,
        "imported_at": imported_at,
        "data_file": COMPRESSED_MUNICIPALITIES_FILENAME if compress else MUNICIPALITIES_FILENAME,
        "record_count": len(records),
        "respondent_count": respondent_count,
        "nonrespondent_count": len(records) - respondent_count,
        "input": {
            "filename": path.name,
            "sha256": hashlib.sha256(input_bytes).hexdigest(),
            "bytes": len(input_bytes),
        },
        "sheet": {
            "name": SHEET_NAME,
            "sections_row": 10,
            "codes_row": CODES_ROW,
            "labels_row": LABELS_ROW,
            "units_row": UNITS_ROW,
            "first_data_row": DATA_ROW,
            "ibge_column": "B",
            "response_column": "A",
        },
        "ignored_sheets": ignored_sheets,
        "fields": fields,
        "warnings": [
            "As declarações municipais descrevem gestão e existência de serviços. A cobertura populacional e o desempenho operacional são publicados em outros módulos.",
            "Células em branco e o marcador literal null são preservados como ausências distintas.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    if compress:
        _write_compressed(output, records)
    else:
        _atomic_json(output, MUNICIPALITIES_FILENAME, records)
    _atomic_json(output, MANIFEST_FILENAME, manifest)
    if compress:
        (output / MUNICIPALITIES_FILENAME).unlink(missing_ok=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa o módulo Gestão Municipal do SINISA 2024.")
    parser.add_argument("--file", type=Path, required=True, help="Planilha XLSX de Gestão Municipal")
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    parser.add_argument("--compress", action="store_true", help="Grava o catálogo municipal como JSON gzip")
    args = parser.parse_args()
    manifest = import_sinisa(args.file, args.output, compress=args.compress)
    print(f"{manifest['record_count']} municípios importados, {manifest['respondent_count']} respondentes.")


if __name__ == "__main__":
    main()
