"""Public official records stay separate from citizen reports, with original scope."""
from fastapi import APIRouter, Request
from .territories import load_file, municipality

router = APIRouter(tags=["Contexto oficial"])


def snapshot(request, name, code):
    value = load_file(request, f"{name}-{code}.json")
    if value is None:
        return {"available": False, "items": [], "total": None, "notes": "Fonte ainda não sincronizada para este município."}
    failed=any(e.get('source')==name and e.get('municipality_code')==code for e in load_file(request,'services-manifest.json',{}).get('errors',[]))
    unconfigured=name=='transparencia' and not request.app.state.settings.portal_transparencia_api_key
    return {**value, "available": True, "stale":failed or unconfigured, "notes":value.get('notes','')+(' Última tentativa falhou; exibindo o cache anterior.' if failed else '')+(' Chave não configurada neste servidor; somente o snapshot histórico está disponível.' if unconfigured else '')}


def school_items(request, code):
    data = load_file(request, "schools-es.json")
    if data is None or not code.startswith("32"):
        return {"available": False, "items": [], "total": None, "notes": "Camada cobre somente a rede estadual do Espírito Santo."}
    items = []
    for feature in data.get("features", []):
        p = feature["properties"]
        if p["municipality_code"] != code:
            continue
        geometry = feature.get("geometry")
        xy = geometry["coordinates"] if geometry else [None, None]
        items.append({"id": str(feature.get("id") or p["inep_id"]), "name": p["name"], "category": "education", "network": "state", "municipality_code": code, "latitude": xy[1], "longitude": xy[0], "source_url": p.get("source_url", "https://dados.es.gov.br")})
    stale=any(e.get('source')=='sedu-schools' for e in load_file(request,'es-manifest.json',{}).get('errors',[]))
    return {"available": True, "items": items, "total": len(items), "stale":stale,"fetched_at": data.get("fetched_at"), "notes": "SEDU/ES: apenas escolas da rede estadual. Código INEP é identificador; este cadastro não substitui o Censo Escolar nacional completo."+(' Última coleta falhou; exibindo o cache anterior.' if stale else '')}


def context(request, code):
    municipality(request, code)
    ombudsman = load_file(request, "ombudsman-es.json")
    omb = {"available": False, "total": None, "by_type": {}, "by_status": {}, "notes": "Sem base estadual sincronizada para este município."}
    if ombudsman and code.startswith("32"):
        omb = {"available": True, "year": ombudsman["year"], "quality": ombudsman.get("quality"), "source_url": ombudsman.get("source_url"), "fetched_at": ombudsman.get("fetched_at"), "notes": ombudsman.get("notes", "Município informado no registro da ouvidoria estadual; não é o local georreferenciado de uma ocorrência."), **ombudsman["municipalities"].get(code, {"total": 0, "by_type": {}, "by_status": {}})}
    sinisa = load_file(request, "sinisa-municipalities.json", {})
    record = sinisa.get(code)
    return {"municipality_code": code, "health": snapshot(request, "cnes", code), "works": snapshot(request, "obrasgov", code), "funding": snapshot(request, "transparencia", code), "education": school_items(request, code), "sanitation_management": {"available": record is not None, "record": record, "manifest": load_file(request, "sinisa-manifest.json", {}), "notes": "SINISA Gestão Municipal, edição 2024, referência 2023. Declarações municipais de gestão; não representam cobertura por bairro."}, "ombudsman": omb, "falabr": {"available": False, "authentication_required": True, "documentation_url": "https://falabr.cgu.gov.br/help", "public_dashboard_url": "https://centralpaineis.cgu.gov.br/visualizar/resolveu", "notes": "A API operacional exige conta webservice e token autorizados pela CGU. O Painel Resolveu é público; a ouvidoria estadual exibida aqui é outra base."}}


def context_indicators(request, code):
    sinisa = load_file(request, "sinisa-municipalities.json", {}).get(code)
    return sinisa.get("indicators", []) if sinisa else []


@router.get("/territories/{code}/context")
def public_context(code: str, request: Request):
    return context(request, code)


@router.get("/territories/{code}/facilities")
def facilities(code: str, request: Request):
    data = context(request, code)
    features = []
    from .territories import geometry
    from shapely.geometry import shape,Point
    from shapely.ops import unary_union
    from shapely.prepared import prep
    boundary=geometry(request,code)
    prepared=None
    if boundary:
        polygon=unary_union([shape(f['geometry']) for f in boundary['features']]) if boundary.get('type')=='FeatureCollection' else shape(boundary.get('geometry',boundary))
        prepared=prep(polygon.buffer(.002))
    quality={'outside_boundary':0,'missing_coordinates':0,'boundary_check':'official' if prepared else 'not_available'}
    for section, kind in [("health", "health"), ("education", "education"), ("works", "work")]:
        for item in data[section]["items"]:
            lat, lng = item.get("latitude"), item.get("longitude")
            if lat is None or lng is None:
                quality['missing_coordinates']+=1
                continue
            if prepared and not prepared.covers(Point(lng,lat)):
                quality['outside_boundary']+=1
                continue
            features.append({"type": "Feature", "id": kind + "-" + item["id"], "geometry": {"type": "Point", "coordinates": [lng, lat]}, "properties": {"id": item["id"], "name": item["name"], "category": item["category"], "kind": kind, "source_url": item.get("source_url"), "attends_sus": item.get("attends_sus"), "status": item.get("status")}})
    return {"type": "FeatureCollection", "features": features,"quality":quality}


def augment_sources(request, original):
    result = {s["id"]: dict(s) for s in original}
    root = request.app.state.settings.official_dir
    for prefix, id_, name, org, url, granularity, notes in [
        ("cnes", "cnes", "CNES · estabelecimentos ativos", "Ministério da Saúde", "https://apidadosabertos.saude.gov.br/v1/#/CNES/get_cnes_estabelecimentos", "establishment", "Registros ativos, públicos e privados, dos municípios piloto. Cadastro não garante disponibilidade de atendimento."),
        ("obrasgov", "obrasgov", "Obrasgov · projetos de investimento", "Ministério da Gestão", "https://api-publica.obrasgov.gestao.gov.br/obras/docs", "project", "Projetos vinculados ao município pela geometria oficial. Valores previstos não são despesas efetivamente pagas."),
        ("transparencia", "portal-transparencia", "Portal da Transparência · convênios", "CGU", "https://api.portaldatransparencia.gov.br/swagger-ui/index.html", "municipality", "Convênios federais com filtro de vigência de 2020 a 2030. Chave usada exclusivamente no backend.")]:
        values = [load_file(request, p.name) for p in root.glob(f"{prefix}-*.json")]
        if values:
            result[id_] = {"id": id_, "name": name, "organization": org, "url": url, "description": notes, "status": "active", "last_synced": max(v["fetched_at"] for v in values), "reference": "Cadastro consultado na data da coleta", "granularity": granularity, "records": sum(v["total"] for v in values), "notes": notes}
    manifest = load_file(request, "sinisa-manifest.json")
    if manifest:
        result["sinisa"] = {"id": "sinisa", "name": "SINISA · Gestão Municipal", "organization": "Ministério das Cidades", "url": manifest["source_url"], "description": "Informações e indicadores de gestão municipal importados da planilha oficial.", "status": "active", "last_synced": manifest.get("imported_at"), "reference": "Edição 2024 · referência 2023", "granularity": "municipality", "records": manifest["record_count"], "notes": "Fonte enviada pelo usuário, validada por código IBGE, cabeçalhos e SHA-256. Células ausentes não são zero."}
    schools = load_file(request, "schools-es.json")
    if schools:
        result["sedu-es"] = {"id": "sedu-es", "name": "Escolas da rede estadual do ES", "organization": "SEDU · Governo do Espírito Santo", "url": "https://dados.es.gov.br/dataset/informacoes-referentes-as-unidades-escolares-da-rede-estadual", "description": "Cadastro oficial compacto com nomes, códigos INEP e coordenadas.", "status": "active", "last_synced": schools.get("fetched_at"), "reference": "Cadastro estadual na data da consulta", "granularity": "establishment", "records": len(schools["features"]), "notes": "Somente rede estadual; não representa todas as escolas nem todos os microdados do Censo Escolar. Coordenadas inválidas são mantidas ausentes."}
    omb = load_file(request, "ombudsman-es.json")
    if omb:
        result["ouvidoria-es"] = {"id": "ouvidoria-es", "name": "Ouvidoria estadual · dados agregados", "organization": "Governo do Espírito Santo", "url": omb["source_url"], "description": "Manifestações de 2025 agregadas por município informado, tipo e situação.", "status": "active", "last_synced": omb.get("fetched_at"), "reference": omb["year"], "granularity": "municipality", "records": omb["quality"]["accepted_rows"], "notes": f"{omb['quality']['unmapped_rows']} registros sem vínculo territorial não foram redistribuídos. Não é a base federal do Fala.BR e não publica protocolos ou textos individuais."}
    if "fala-br" in result:
        result["fala-br"]["notes"] = "GET de manifestações retornou HTTP 401 sem token. Exige conta webservice autorizada. Painel público: https://centralpaineis.cgu.gov.br/visualizar/resolveu."
    mappings=[('services-manifest.json',{'cnes':'cnes','obrasgov':'obrasgov','transparencia':'portal-transparencia'}),('es-manifest.json',{'sedu-schools':'sedu-es','ouvidoria-es':'ouvidoria-es'})]
    for manifest_name,ids in mappings:
        for error in load_file(request,manifest_name,{}).get('errors',[]):
            id_=ids.get(error.get('source'))
            if id_ in result:
                result[id_]['stale']=True
                result[id_]['notes']+=' Última tentativa de sincronização falhou; este é o último cache válido.'
    if 'portal-transparencia' in result and not request.app.state.settings.portal_transparencia_api_key:
        result['portal-transparencia']['status']='requires_configuration'
        result['portal-transparencia']['stale']=True
        result['portal-transparencia']['notes']+=' Chave não configurada neste servidor; somente o snapshot histórico está disponível.'
    return list(result.values())
