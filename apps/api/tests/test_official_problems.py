from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Issue, OfficialRecord
from app.algorithms import similarity


def add_official(app):
    with Session(app.state.engine) as db:
        issue=Issue(id="official-theme",title="ReclamaÃƒÂ§ÃƒÂµes sobre falta de ÃƒÂ¡gua",summary="Registros oficiais de reclamaÃƒÂ§ÃƒÂ£o. MunicÃƒÂ­pio informado, sem endereÃƒÂ§o.",category="sanitation",municipality_code="3205002",latitude=None,longitude=None,origin="official",verification_status="official_registered",operational_status="not_assessed",sources=[{"title":"Ouvidoria ES", "url":"https://dados.es.gov.br/dataset/manifestacoes-da-ouvidoria", "publisher":"SECONT/ES", "source_type":"official", "published_at":None}])
        db.add(issue);db.flush()
        for n in range(2):
            db.add(OfficialRecord(id=f"official-{n}",issue_id=issue.id,source_key="ouvidoria-es-2026",year=2026,municipality_code="3205002",subject="Falta de ÃƒÂ¡gua",agency="CESAN",manifestation_type="ReclamaÃƒÂ§ÃƒÂ£o",processing_status="Encerrada",recorded_at="2026-01-01T00:00:00+00:00",source_url="https://dados.es.gov.br/dataset/manifestacoes-da-ouvidoria",fetched_at="2026-11-22T00:00:00+00:00"))
        db.commit()


def test_official_cases_are_not_citizen_reports_or_verified_resolutions(client,app):
    add_official(app)
    counts=client.get("/api/v1/territories/3205002/summary").json()["counts"]
    assert counts["total"]==1 and counts["official_records"]==2
    assert counts["reports"]==0 and counts["resolved"]==0 and counts["unresolved"]==0
    assert counts["not_assessed"]==1
    item=client.get("/api/v1/issues?origin=official").json()["items"][0]
    assert item["origin"]=="official" and item["official_records_count"]==2
    assert item["latitude"] is None and item["longitude"] is None and item["location_precision"]=="municipality"
    assert client.get("/api/v1/issues?origin=community").json()["total"]==0
    assert client.get("/api/v1/issues?bbox=-41,-21,-39,-19").json()["total"]==0
    data=client.get("/api/v1/issues/official-theme").json()
    assert data["official_records_total"]==2 and len(data["official_records"])==2
    assert data["official_records"][0]["processing_status"]=="Encerrada"
    assert data["operational_status"]=="not_assessed"


def test_missing_point_never_creates_fake_distance():
    a={"municipality_code":"3205002","category":"sanitation","latitude":-20.2,"longitude":-40.2,"description":"Falta de agua"}
    b={**a,"latitude":None,"longitude":None}
    result=similarity(a,b)
    assert result["distance_meters"] is None and result["score"]<.65


def test_unlocated_official_themes_do_not_become_costed_physical_interventions(client,app):
    add_official(app)
    r=client.post("/api/v1/simulations",json={"municipality_code":"3205002","category":"sanitation","budget":1000,"unit_cost":100,"strategy":"reports","demo":False})
    assert r.status_code==201
    assert r.json()["selected_count"]==0
    assert r.json()["excluded_official_dossiers"]==1


def test_sqlite_upgrade_preserves_existing_issues_and_accepts_unlocated_official_records(tmp_path):
    from sqlalchemy.schema import CreateTable
    from app.config import Settings
    from app.db import make_engine, initialize_database
    s=Settings(_env_file=None,database_url=f"sqlite:///{(tmp_path/'legacy.db').as_posix()}",official_dir=tmp_path/'official',auth_provider="supabase",seed_demo=False)
    engine=make_engine(s.database_url)
    ddl=str(CreateTable(Issue.__table__).compile(engine))
    ddl="\n".join(line for line in ddl.splitlines() if not line.strip().startswith("origin "))
    ddl=ddl.replace("latitude FLOAT", "latitude FLOAT NOT NULL").replace("longitude FLOAT", "longitude FLOAT NOT NULL")
    with engine.begin() as c:
        c.exec_driver_sql(ddl)
        c.exec_driver_sql("INSERT INTO issues (id,title,summary,category,municipality_code,neighborhood,latitude,longitude,verification_status,operational_status,first_reported_at,last_activity_at,is_demo,version,sources) VALUES ('legacy','Existing','Preserve original','sanitation','3205002','',-20.2,-40.2,'community_report','reported','2026-01-01','2026-01-01',0,1,'[]')")
    initialize_database(engine,s)
    with Session(engine) as db:
        old=db.get(Issue,'legacy')
        assert old.summary=='Preserve original' and old.origin=='community'
        db.add(Issue(id='new-official',title='Official',summary='Municipal',category='sanitation',municipality_code='3205002',latitude=None,longitude=None,origin='official'))
        db.commit()
    engine.dispose()


def test_thematic_source_dossiers_cannot_be_merged_as_unique_physical_incidents(client,app):
    from conftest import login
    add_official(app)
    with Session(app.state.engine) as db:
        db.add(Issue(id="community-target",title="Community",summary="Specific point",category="sanitation",municipality_code="3205002",latitude=-20.2,longitude=-40.2))
        db.commit()
    login(client,True)
    r=client.post("/api/v1/admin/issues/official-theme/merge",json={"target_id":"community-target","reason":"Teste de proteção de escopo de um dossiê temático."})
    assert r.status_code==422
    assert client.get("/api/v1/territories/3205002/summary").json()["counts"]["official_records"]==2
