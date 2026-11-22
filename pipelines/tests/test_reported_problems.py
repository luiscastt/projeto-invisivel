import gzip
import json
import hashlib

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from pipelines import reported_problems as pipeline

CATALOG = {'municipalities': [
    {'code': '3205002', 'name': 'Serra', 'state_abbreviation': 'ES'},
    {'code': '3205309', 'name': 'Vitória', 'state_abbreviation': 'ES'},
    {'code': '2616209', 'name': 'Vitória', 'state_abbreviation': 'PE'},
]}
RESOURCE = pipeline.RESOURCES[2026]
FETCHED = '2026-11-22T12:00:00Z'


def row(**changes):
    return {'_id': 1, 'Ano': 2026, 'Municipio': 'Serra',
            'TipoManifestacao': 'Reclamação', 'Orgao': 'CESAN',
            'Assunto': 'Vazamento de Água', 'Situacao': 'Encerrada',
            'DataRegistro': '2026-01-01T00:00:00', 'DataSituacao': None,
            'Protocolo': 'SECRET-PROTOCOL', 'Texto': 'SECRET-PERSON-NAME', **changes}


def snapshot(rows):
    return pipeline.normalize_records({RESOURCE: rows}, CATALOG, FETCHED)


def test_only_explicit_collective_complaints_are_accepted_without_private_data():
    result = snapshot([
        row(), row(_id=2, TipoManifestacao='Elogio'),
        row(_id=3, TipoManifestacao='Solicitação'), row(_id=4, TipoManifestacao='Denúncia'),
        row(_id=5, Orgao='SEDU', Assunto='Pagamento a Servidor Público'),
        row(_id=6, Assunto='Conta de Água com valor indevido'),
        row(_id=7, Assunto='Assunto desconhecido'), row(_id=8, Municipio='Todo Estado'),
        row(_id=9, Orgao='BANESTES'), row(_id=10, Ano=2024),
    ])
    assert len(result['records']) == 1
    assert result['quality']['accepted_rows'] == 1
    assert sum(result['quality']['rejected_by_reason'].values()) == 9
    serialized = json.dumps(result)
    assert 'SECRET-' not in serialized
    assert 'Protocolo' not in serialized and 'DataSituacao' not in serialized
    assert set(result['records'][0]) == {
        'id', 'issue_id', 'source_key', 'year', 'municipality_code', 'subject', 'agency',
        'manifestation_type', 'processing_status', 'recorded_at', 'source_url', 'fetched_at',
    }


def test_dossiers_group_exact_normalized_subject_agency_year_and_declared_municipality():
    result = snapshot([row(), row(_id=2, Assunto=' VAZAMENTO DE ÁGUA '),
                       row(_id=3, Municipio='Vitória'), row(_id=4, Orgao='ARSP')])
    assert len(result['issues']) == 3
    first_id = hashlib.sha256(f'{RESOURCE}|1'.encode()).hexdigest()
    second_id = hashlib.sha256(f'{RESOURCE}|2'.encode()).hexdigest()
    record_index = {r['id']: r for r in result['records']}
    group = next(issue for issue in result['issues'] if issue['id'] == record_index[first_id]['issue_id'])
    assert record_index[second_id]['issue_id'] == group['id']
    assert group['latitude'] is None and group['longitude'] is None
    assert group['verification_status'] == 'official_registered'
    assert group['operational_status'] == 'not_assessed'
    assert group['origin'] == 'official'
    assert sum(record['issue_id'] == group['id'] for record in result['records']) == 2
    assert 'Reclamações registradas oficialmente' in group['summary']
    assert 'não significa' in group['summary']
    assert 'endereço' in group['summary']
    assert len(group['title']) <= 180
    source = group['sources'][0]
    assert set(source) == {'id', 'title', 'url', 'publisher', 'source_type', 'published_at', 'checked_at'}
    assert source['source_type'] == 'official'
    assert source['published_at'] is None and source['checked_at'] == FETCHED
    assert snapshot([row()])['records'][0]['id'] == first_id
    assert snapshot([row()])['issues'][0]['id'] == group['id']


@pytest.mark.parametrize(('agency', 'subject', 'category'), [
    ('CESAN', 'Vazamento/Obstrução de Esgoto', 'sanitation'),
    ('CESAN', 'Despejo Ou Descarte De Resíduos', 'sanitation'),
    ('CETURB', 'Transporte Público', 'mobility'),
    ('SEDU', 'Merenda Escolar', 'education'),
    ('SESA', 'Saúde Pública', 'health'),
    ('DER', 'Buracos em via pública', 'infrastructure'),
    ('IEMA', 'Poluição Ambiental', 'environment'),
])
def test_reviewed_subject_agency_mapping(agency, subject, category):
    assert snapshot([row(Orgao=agency, Assunto=subject)])['issues'][0]['category'] == category


def test_import_is_idempotent_and_refresh_preserves_moderation_and_user_sources(tmp_path):
    from app.db import Base
    from app.models import IngestionJob, Issue, OfficialRecord
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'snapshot.json.gz'
    original = snapshot([row()])
    path.write_bytes(gzip.compress(json.dumps(original).encode()))
    with Session(engine) as db:
        first = pipeline.import_snapshot(db, path)
        db.commit()
        assert first['issues_created'] == 1
        second = pipeline.import_snapshot(db, path)
        assert second['skipped'] is True
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 1
        issue = db.get(Issue, original['issues'][0]['id'])
        issue.verification_status = 'verified'
        issue.operational_status = 'resolved'
        issue.title = 'Título revisto pelo moderador'
        issue.sources = [*issue.sources, {'url': 'https://example.org/community', 'label': 'Cidadão'}]
        db.commit()
        refreshed = snapshot([row(Situacao='Em tratamento'), row(_id=2)])
        path.write_bytes(gzip.compress(json.dumps(refreshed).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.verification_status == 'verified'
        assert issue.operational_status == 'resolved'
        assert issue.title == 'Título revisto pelo moderador'
        assert any(source['url'] == 'https://example.org/community' for source in issue.sources)
        assert db.scalar(select(func.count()).select_from(Issue)) == 1
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 2
        record = db.get(OfficialRecord, original['records'][0]['id'])
        assert record.processing_status == 'Em tratamento'
        assert db.scalar(select(func.count()).select_from(IngestionJob)) == 2


def test_fetch_requests_only_allowlisted_columns_and_keeps_catalog_metadata():
    import httpx
    requests = []
    def handle(request):
        requests.append(request)
        if request.url.path.endswith('package_show'):
            return httpx.Response(200, json={'success': True, 'result': {
                'organization': {'title': 'SECONT-ES'}, 'metadata_modified': '2026-11-19',
                'license_title': 'CC0', 'resources': [
                    {'id': resource, 'name': f'Ouvidoria {year}', 'datastore_active': True,
                     'last_modified': '2026-11-19'} for year, resource in pipeline.RESOURCES.items()
                ],
            }})
        assert request.url.params['fields'] == ','.join(pipeline.FIELDS)
        assert request.url.params['sort'] == '_id asc'
        assert request.url.params['offset'] == '0'
        year = next(year for year, resource in pipeline.RESOURCES.items()
                    if resource == request.url.params['resource_id'])
        return httpx.Response(200, json={'success': True, 'result': {
            'total': 1, 'total_was_estimated': False, 'records': [row(Ano=year)],
        }})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = pipeline.fetch_snapshot(CATALOG, client)
    assert len(result['records']) == 2
    assert len(requests) == 3
    assert result['resources'][0]['publisher'] == 'SECONT-ES'
    assert 'SECRET-' not in json.dumps(result)


def test_rejects_duplicate_conflicting_source_ids():
    with pytest.raises(ValueError, match='divergente'):
        snapshot([row(), row(Situacao='Em tratamento')])

def test_refresh_removes_only_managed_records_and_retires_empty_dossiers(tmp_path):
    from app.db import Base
    from app.models import Audit, Issue, OfficialRecord
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    older_resource = pipeline.RESOURCES[2025]
    initial = pipeline.normalize_records({RESOURCE: [row()], older_resource: [row(Ano=2025)]}, CATALOG, FETCHED)
    path = tmp_path / 'refresh.json.gz'
    def write(value):
        path.write_bytes(gzip.compress(json.dumps(value).encode()))
    with Session(engine) as db:
        write(initial)
        pipeline.import_snapshot(db, path)
        db.commit()
        removed_id = next(r['issue_id'] for r in initial['records'] if r['year'] == 2026)
        retained_id = next(r['issue_id'] for r in initial['records'] if r['year'] == 2025)
        write(snapshot([]))
        result = pipeline.import_snapshot(db, path)
        db.commit()
        assert result['records_removed'] == 1
        assert result['issues_source_removed'] == 1
        assert db.get(Issue, removed_id).operational_status == 'source_removed'
        assert db.get(Issue, retained_id).operational_status == 'not_assessed'
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 1
        assert db.scalar(select(OfficialRecord.source_key)) == older_resource
        assert db.scalar(select(func.count()).select_from(Audit)) == 1
        write(snapshot([row()]))
        restored = pipeline.import_snapshot(db, path)
        db.commit()
        assert restored['issues_restored'] == 1
        assert db.get(Issue, removed_id).operational_status == 'not_assessed'
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 2
        assert db.scalar(select(func.count()).select_from(Audit)) == 2


def test_reclassified_record_moves_group_and_retires_only_empty_previous_group(tmp_path):
    from app.db import Base
    from app.models import Issue, OfficialRecord
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    old = snapshot([row()])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(old).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        moved = snapshot([row(Assunto='Rede De Esgoto')])
        path.write_bytes(gzip.compress(json.dumps(moved).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        assert db.get(OfficialRecord, old['records'][0]['id']).issue_id == moved['issues'][0]['id']
        assert db.get(Issue, old['issues'][0]['id']).operational_status == 'source_removed'
        assert db.get(Issue, moved['issues'][0]['id']).operational_status == 'not_assessed'
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 1


@pytest.mark.parametrize('protection', ['human_status', 'human_verification', 'approved_citizen_report'])
def test_empty_source_dossier_preserves_human_decisions_and_approved_reports(tmp_path, protection):
    from app.db import Base
    from app.models import Issue, OfficialRecord, Report, User
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    initial = snapshot([row()])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(initial).encode()))
        pipeline.import_snapshot(db, path)
        issue = db.get(Issue, initial['issues'][0]['id'])
        if protection == 'human_status':
            issue.operational_status = 'resolved'
        elif protection == 'human_verification':
            issue.verification_status = 'verified'
        else:
            user = User(id='citizen', email='citizen@example.org', display_name='Cidadão')
            db.add(user)
            db.flush()
            db.add(Report(id='report', tracking_code='TEST-1', author_id=user.id,
                          issue_id=issue.id, moderation_status='approved', payload={}))
        db.commit()
        expected_status = issue.operational_status
        expected_verification = issue.verification_status
        path.write_bytes(gzip.compress(json.dumps(snapshot([])).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.operational_status == expected_status
        assert issue.verification_status == expected_verification
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 0
        assert db.scalar(select(func.count()).select_from(Issue)) == 1
        if protection == 'approved_citizen_report':
            assert db.get(Report, 'report').issue_id == issue.id


def test_refresh_native_source_metadata_preserves_user_sources_and_manual_edits(tmp_path):
    from app.db import Base
    from app.models import Issue
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    initial = snapshot([row()])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(initial).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        issue = db.get(Issue, initial['issues'][0]['id'])
        user_source = {'id': 'community-1', 'url': 'https://example.org/community',
                       'title': 'Fonte do cidadão', 'publisher': 'Comunidade',
                       'source_type': 'community', 'published_at': None, 'checked_at': None}
        issue.sources = [*issue.sources, user_source]
        db.commit()
        updated = pipeline.normalize_records({RESOURCE: [row()]}, CATALOG, '2026-11-23T12:00:00Z')
        path.write_bytes(gzip.compress(json.dumps(updated).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.sources[0]['checked_at'] == '2026-11-23T12:00:00Z'
        assert issue.sources[1] == user_source
        edited = {**issue.sources[0], 'title': 'Título da fonte revisto pela moderação'}
        issue.sources = [edited, user_source]
        db.commit()
        newer = pipeline.normalize_records({RESOURCE: [row()]}, CATALOG, '2026-11-24T12:00:00Z')
        path.write_bytes(gzip.compress(json.dumps(newer).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.sources == [edited, user_source]

def test_source_dates_advance_for_new_complaints_but_preserve_newer_human_activity(tmp_path):
    from app.db import Base
    from app.models import Issue
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    initial = snapshot([row(DataRegistro='2026-01-10T00:00:00')])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(initial).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        issue = db.get(Issue, initial['issues'][0]['id'])
        updated = snapshot([row(DataRegistro='2026-01-10T00:00:00'),
                            row(_id=2, DataRegistro='2026-02-01T00:00:00')])
        path.write_bytes(gzip.compress(json.dumps(updated).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.last_activity_at == '2026-02-01T00:00:00'
        assert issue.first_reported_at == '2026-01-10T00:00:00'
        issue.last_activity_at = '2026-03-01T00:00:00Z'
        db.commit()
        updated = snapshot([row(DataRegistro='2026-01-10T00:00:00'),
                            row(_id=2, DataRegistro='2026-02-01T00:00:00'),
                            row(_id=3, DataRegistro='2026-01-05T00:00:00')])
        path.write_bytes(gzip.compress(json.dumps(updated).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.last_activity_at == '2026-03-01T00:00:00Z'
        assert issue.first_reported_at == '2026-01-05T00:00:00'
        assert issue.operational_status == 'not_assessed'


def test_reclassification_outside_allowed_scope_removes_the_old_record(tmp_path):
    from app.db import Base
    from app.models import Issue, OfficialRecord
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    initial = snapshot([row()])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(initial).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        rejected = snapshot([row(Assunto='Conta de Água com valor indevido')])
        assert rejected['quality']['total_rows'] == 1
        assert rejected['quality']['accepted_rows'] == 0
        path.write_bytes(gzip.compress(json.dumps(rejected).encode()))
        result = pipeline.import_snapshot(db, path)
        db.commit()
        assert result['records_removed'] == 1
        assert db.scalar(select(func.count()).select_from(OfficialRecord)) == 0
        assert db.get(Issue, initial['issues'][0]['id']).operational_status == 'source_removed'

@pytest.mark.parametrize('invalid_date', ['2026-12-07T00:00:00', '07/12/2026', '2026-02-30T00:00:00', 'not-a-date'])
def test_future_and_malformed_source_dates_never_become_report_timestamps(invalid_date):
    result = snapshot([row(DataRegistro=invalid_date)])
    assert result['records'][0]['recorded_at'] is None
    assert result['issues'][0]['first_reported_at'] is None
    assert result['issues'][0]['last_activity_at'] == FETCHED
    assert result['quality']['future_date_rows'] == int(invalid_date.startswith('2026-12-07'))
    assert result['quality']['malformed_date_rows'] == int(not invalid_date.startswith('2026-12-07'))
    assert invalid_date not in json.dumps(result)


def test_valid_dates_preserve_source_exact_string_without_timezone_guessing():
    result = snapshot([row(DataRegistro='2026-11-22T23:59:59'),
                       row(_id=2, DataRegistro='2026-01-01T00:00:00')])
    assert {r['recorded_at'] for r in result['records']} == {'2026-11-22T23:59:59', '2026-01-01T00:00:00'}
    assert result['issues'][0]['first_reported_at'] == '2026-01-01T00:00:00'
    assert result['issues'][0]['last_activity_at'] == '2026-11-22T23:59:59'
    assert result['quality']['future_date_rows'] == 0
    assert result['quality']['malformed_date_rows'] == 0


def test_nullable_unknown_first_date_refreshes_to_first_valid_official_date(tmp_path):
    from app.db import Base
    from app.models import Issue
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    path = tmp_path / 'refresh.json.gz'
    initial = snapshot([row(DataRegistro=None)])
    with Session(engine) as db:
        path.write_bytes(gzip.compress(json.dumps(initial).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        issue = db.get(Issue, initial['issues'][0]['id'])
        assert issue.first_reported_at is None
        later = snapshot([row(DataRegistro=None), row(_id=2, DataRegistro='2026-01-01T00:00:00')])
        path.write_bytes(gzip.compress(json.dumps(later).encode()))
        pipeline.import_snapshot(db, path)
        db.commit()
        db.refresh(issue)
        assert issue.first_reported_at == '2026-01-01T00:00:00'

def test_sync_collection_failure_preserves_previous_snapshot_and_manifest(tmp_path, monkeypatch):
    output = tmp_path / 'reported-problems-es.json.gz'
    manifest_path = tmp_path / 'reported-problems-manifest.json'
    output.write_bytes(b'previous-good-snapshot')
    manifest_path.write_bytes(b'previous-good-manifest')
    def fail(catalog, client=None):
        raise RuntimeError('official service unavailable')
    monkeypatch.setattr(pipeline, 'fetch_snapshot', fail)
    with pytest.raises(RuntimeError, match='unavailable'):
        pipeline.sync_reported_problems(output=output, catalog=CATALOG)
    assert output.read_bytes() == b'previous-good-snapshot'
    assert manifest_path.read_bytes() == b'previous-good-manifest'
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted([output.name, manifest_path.name])


def test_sync_returns_manifest_for_atomically_written_snapshot(tmp_path, monkeypatch):
    output = tmp_path / 'reported-problems-es.json.gz'
    (tmp_path / 'catalog.json').write_text(json.dumps(CATALOG), encoding='utf-8')
    expected = snapshot([row()])
    def collect(catalog, client=None):
        assert catalog == CATALOG
        return expected
    monkeypatch.setattr(pipeline, 'fetch_snapshot', collect)
    manifest = pipeline.sync_reported_problems(output=output)
    assert json.loads(gzip.decompress(output.read_bytes())) == expected
    assert manifest['snapshot_sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert json.loads((tmp_path / 'reported-problems-manifest.json').read_text(encoding='utf-8')) == manifest
    assert not any(path.is_dir() for path in tmp_path.iterdir())
