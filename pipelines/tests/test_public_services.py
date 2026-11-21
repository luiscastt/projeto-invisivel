import pytest
from pipelines.public_services import normalize_cnes, normalize_works, normalize_funding, collect_cnes, collect_funding, sync_services


def test_cnes_requires_municipality_and_removes_contact_personal_fields():
    rows = [{"codigo_cnes": 123, "codigo_municipio": 320500, "nome_fantasia": "UBS de teste", "latitude_estabelecimento_decimo_grau": -20.2, "longitude_estabelecimento_decimo_grau": -40.3, "endereco_email_estabelecimento": "private@example.com", "numero_telefone_estabelecimento": "999999999", "estabelecimento_faz_atendimento_ambulatorial_sus": "SIM", "data_atualizacao": "2025-09-03"}]
    result = normalize_cnes(rows, "3205002")
    assert result[0]["id"] == "0000123"
    assert result[0]["attends_sus"] is True
    assert "email" not in str(result)
    assert "private@example.com" not in str(result)
    assert "999999999" not in str(result)
    assert normalize_cnes([{**rows[0], "latitude_estabelecimento_decimo_grau": 0}], "3205002")[0]["latitude"] is None
    with pytest.raises(ValueError):
        normalize_cnes([{**rows[0], "codigo_municipio": 320530}], "3205002")


def test_cnes_offset_is_page_not_record_offset_and_has_repeat_protection():
    calls = []
    def fetch(url, params=None, headers=None):
        calls.append(params["offset"])
        return {"estabelecimentos": [{"codigo_cnes": i + 1, "codigo_municipio": 320500, "nome_fantasia": "Unidade"} for i in range(20)] if params["offset"] == 0 else []}
    assert len(collect_cnes("3205002", fetch)) == 20
    assert calls == [0, 1]


def test_works_keep_project_identity_and_official_missing_coordinates():
    projects = [{"id_projeto_investimento": "ABC", "desc_nome": "Construção de UBS", "situacao": "Em execução", "pins": [{"latitude": "-20.2", "longitude": "-40.3"}], "investimentos_previstos": [{"vl_investimento_previsto": 1500}], "ano_cadastro": 2025, "eixos_tipos": [{"tipo": "Saúde"}]}]
    result = normalize_works(projects, "3205002")
    assert result[0]["id"] == "ABC"
    assert result[0]["category"] == "health"
    assert result[0]["planned_investment"] == 1500
    assert normalize_works([{**projects[0], "pins": []}], "3205002")[0]["latitude"] is None


def test_funding_validates_code_and_never_publishes_cpf_or_secret():
    row = {"id": 1, "municipioConvenente": {"codigoIBGE": "3205002"}, "dimConvenio": {"objeto": "Reforma pública", "numero": "1/2025"}, "valor": 100, "valorLiberado": 50, "dataReferencia": "1900-01-01", "dataInicioVigencia": "2025-01-01", "convenente": {"cpfFormatado": "123.456.789-00"}}
    result = normalize_funding([row], "3205002")
    assert result[0]["reference_date"] is None
    assert result[0]["amount"] == 100
    assert "cpf" not in str(result).lower()
    with pytest.raises(ValueError):
        normalize_funding([row], "3205309")


def test_failed_sources_preserve_last_good_snapshot_without_secret(tmp_path):
    (tmp_path / "cnes-3205002.json").write_text('{"items": [], "fetched_at": "last-good"}')
    def fail(url, params=None, headers=None):
        raise RuntimeError("upstream unavailable")
    result = sync_services(tmp_path, codes=["3205002"], fetch=fail, transparency_key="test-secret")
    assert (tmp_path / "cnes-3205002.json").read_text() == '{"items": [], "fetched_at": "last-good"}'
    assert result["errors"]
    assert "test-secret" not in str(result)


def test_transparency_requires_both_dates_in_filter():
    def fetch(url, params=None, headers=None):
        assert params["dataVigenciaInicial"] == "01/01/2020"
        assert params["dataVigenciaFinal"] == "31/12/2030"
        assert headers == {"chave-api-dados": "secret"}
        return []
    assert collect_funding("3205002", fetch, "secret") == []


def test_missing_key_records_skipped_refresh_without_faking_collection(tmp_path, monkeypatch):
    monkeypatch.delenv('PORTAL_TRANSPARENCIA_API_KEY',raising=False)
    def fetch(url,params=None,headers=None):
        return {'estabelecimentos':[]} if 'saude' in url else {'data':[],'total_pages':1,'total_items':0}
    result=sync_services(tmp_path,codes=['3205002'],fetch=fetch)
    skipped=next(j for j in result['jobs'] if j['source']=='transparencia')
    assert skipped['status']=='requires_configuration'
    assert not (tmp_path/'transparencia-3205002.json').exists()
