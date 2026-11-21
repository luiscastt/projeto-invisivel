import gzip
import hashlib
import json

import pytest
from openpyxl import Workbook


@pytest.fixture
def workbook(tmp_path):
    path = tmp_path / "sinisa.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = "GM"
    sheet["C3"] = "Diagnóstico de Gestão Municipal - 2024"
    sheet["A11"] = "Respondeu ao Módulo Gestão Municipal do SINISA 2024"
    sheet["A13"] = "(sim/não)"
    sheet["B11"] = "Cod_IBGE"
    sheet["C11"] = "Município"
    sheet["D11"] = "UF"
    columns = {
        "AM": ("OGM4204", "Investimento total realizado pelo Município para o serviço de abastecimento de água", "(R$/ano)"),
        "AZ": ("OGM4304", "Investimento total realizado pelo Município para o serviço de esgotamento sanitário", "(R$/ano)"),
        "BI": ("OGM1001*", "Existência de prestação de serviço público de abastecimento de água com rede de distribuição no município.", "(sim/não)"),
        "BK": ("OGM1101*", "Existência de prestação de serviço público de esgotamento sanitário com rede coletora (independentemente de existir tratamento de esgoto).", "(sim/não)"),
        "BQ": ("OGM2001*", "Existência de entidade responsável pela regulação de serviços de abastecimento de água", "(sim/não)"),
        "BS": ("OGM2101*", "Existência de entidade responsável pela regulação de serviços de esgotamento sanitário", "(sim/não)"),
        "BY": ("OGM3001*", "Existência de Lei que institui a Política Municipal de Saneamento Básico, conforme a Lei Federal nº 11.445/2007 ", "(sim/não)"),
        "CC": ("OGM3004*", "Existência de Plano de Saneamento Básico (municipal e/ou regional), conforme a Lei Federal nº 11.445/2007", "(sim/não)"),
        "CD": ("OGM3005*", "instrumento de aprovação do Plano de Saneamento Básico", None),
        "CE": ("OGM3006*", "Número do instrumento de aprovação do Plano de Saneamento Básico", None),
        "CF": ("OGM3007*", "Data da promulgação do instrumento de aprovação do Plano de Saneamento Básico", None),
        "CG": ("OGM3008*", "Componentes abrangidos pelo Plano de Saneamento Básico", None),
        "CI": ("OGM3010*", "Área(s) do município abrangida(s) pelo Plano de Saneamento Básico?", "(urbana/rural)"),
        "CL": ("OGM3013*", "Existência de Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS), conforme a Lei Federal nº 12.305/2010", "(sim/não)"),
        "DD": ("OGM3201*", "Existência de Conselho Municipal com atuação específica para os serviços de saneamento básico", "(sim/não)"),
    }
    for column, (code, label, unit) in columns.items():
        sheet[f"{column}11"] = code
        sheet[f"{column}12"] = label
        if unit:
            sheet[f"{column}13"] = unit

    sheet["BJ11"] = "Quantidade de prestadores de Abastecimento de Água atuando no município"
    sheet["BL11"] = "Quantidade de prestadores de Esgoto atuando no município"
    sheet["A15"], sheet["B15"], sheet["C15"], sheet["D15"] = "Não", 1100015, "Alta Floresta D Oeste", "RO"
    sheet["A16"], sheet["B16"], sheet["C16"], sheet["D16"] = "Sim", "3205002", "Serra", "ES"
    for column in [*columns, "BJ", "BL"]:
        sheet[f"{column}15"] = "null"
    sheet["AM16"] = " 1.234,50"
    sheet["BI16"] = "Sim"
    sheet["BJ16"] = 1
    sheet["BK16"] = "Não"
    sheet["BL16"] = 0
    sheet["BY16"] = "Não"
    sheet["CC16"] = "Sim"
    sheet["CE16"] = "004010"
    sheet["CG16"] = "1-Abastecimento de água \n2-Esgotamento sanitário \n"
    book.create_sheet("Detalhamento Prestadores Serv").append([3205002, "Uma linha de prestador"])
    book.save(path)
    return path, book, sheet


def test_import_preserves_response_categories_and_distinct_missing_markers(workbook, tmp_path):
    from pipelines.sinisa import import_sinisa

    path, _, _ = workbook
    output = tmp_path / "official"
    manifest = import_sinisa(path, output)
    records = json.loads((output / "sinisa-municipalities.json").read_bytes())
    assert set(records) == {"1100015", "3205002"}
    assert records["3205002"]["source"]["row"] == 16
    assert records["3205002"]["municipality_code"] == "3205002"
    assert records["3205002"]["reference_year"] == "2023"
    assert records["3205002"]["responded"] is True
    assert records["1100015"]["responded"] is False
    answered = {field["code"]: field for field in records["3205002"]["information"]}
    unanswered = {field["code"]: field for field in records["1100015"]["information"]}
    assert answered["OGM3001"]["value"] == "Não"
    assert answered["OGM3001"]["label"].endswith("Lei Federal nº 11.445/2007")
    assert answered["OGM3006"]["value"] == "004010"
    assert answered["OGM3008"]["value"] == "1-Abastecimento de água \n2-Esgotamento sanitário"
    assert answered["OGM4304"]["value"] is None
    assert answered["OGM4304"]["missing_reason"] == "blank"
    assert unanswered["OGM4304"]["value"] is None
    assert unanswered["OGM4304"]["missing_reason"] == "nonrespondent"
    assert manifest == json.loads((output / "sinisa-manifest.json").read_bytes())
    assert manifest["input"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert manifest["input"]["filename"] == "sinisa.xlsx"
    assert manifest["record_count"] == 2
    assert manifest["respondent_count"] == 1
    assert manifest["edition"] == "2024"
    assert manifest["reference_year"] == "2023"
    assert manifest["sheet"]["labels_row"] == 12
    assert manifest["fields"]["OGM3001"]["column"] == "BY"


def test_numeric_indicators_preserve_reported_zero_and_normalize_brazilian_currency(workbook, tmp_path):
    from pipelines.sinisa import import_sinisa

    output = tmp_path / "official"
    import_sinisa(workbook[0], output)
    records = json.loads((output / "sinisa-municipalities.json").read_bytes())
    indicators = {item["id"]: item for item in records["3205002"]["indicators"]}
    sewer_count = indicators["sinisa-gm-sewer-provider-count"]
    assert (sewer_count["value"], sewer_count["quality"], sewer_count["year"]) == (0, "official", "2023")
    assert sewer_count["name"] == "Quantidade de prestadores de Esgoto atuando no município"
    water_investment = indicators["sinisa-gm-ogm4204"]
    assert (water_investment["value"], water_investment["unit"]) == (1234.5, "R$/ano")
    assert indicators["sinisa-gm-ogm4304"]["value"] is None
    assert indicators["sinisa-gm-ogm4304"]["quality"] == "unavailable"
    assert all(item["value"] is None for item in records["1100015"]["indicators"])


def test_duplicate_ibge_codes_do_not_replace_existing_snapshot(workbook, tmp_path):
    from pipelines.sinisa import import_sinisa

    path, book, sheet = workbook
    output = tmp_path / "official"
    import_sinisa(path, output)
    snapshot = output / "sinisa-municipalities.json"
    original = snapshot.read_bytes()
    sheet["B16"] = "1100015"
    book.save(path)
    with pytest.raises(ValueError, match="duplicado.*1100015"):
        import_sinisa(path, output)
    assert snapshot.read_bytes() == original


def test_compressed_snapshot_matches_json_and_replaces_previous_format(workbook, tmp_path):
    from pipelines.sinisa import import_sinisa

    output = tmp_path / "official"
    raw_path = output / "sinisa-municipalities.json"
    compressed_path = output / "sinisa-municipalities.json.gz"
    import_sinisa(workbook[0], output)
    raw_records = json.loads(raw_path.read_bytes())

    manifest = import_sinisa(workbook[0], output, compress=True)
    compressed_bytes = compressed_path.read_bytes()
    assert compressed_bytes[4:8] == b"\x00" * 4
    compressed_records = json.loads(gzip.decompress(compressed_bytes))
    assert set(compressed_records) == set(raw_records)
    assert compressed_records["3205002"]["information"] == raw_records["3205002"]["information"]
    assert manifest["data_file"] == compressed_path.name
    assert not raw_path.exists()

    manifest = import_sinisa(workbook[0], output)
    assert raw_path.exists()
    assert manifest["data_file"] == raw_path.name


@pytest.mark.parametrize(("cell", "value", "error"), [
    ("C3", "Diagnóstico de Gestão Municipal - 2025", "2024"),
    ("CC11", "OGM3201*", "OGM3004"),
    ("B16", "320500", "IBGE"),
])
def test_rejects_unexpected_workbook_layout_or_identifier(workbook, tmp_path, cell, value, error):
    from pipelines.sinisa import import_sinisa

    path, book, sheet = workbook
    sheet[cell] = value
    book.save(path)
    output = tmp_path / "official"
    with pytest.raises(ValueError, match=error):
        import_sinisa(path, output)
    assert not (output / "sinisa-municipalities.json").exists()
