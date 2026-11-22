"""Public SECONT complaint dossiers; no narratives, protocols or incident coordinates.

A dossier is a thematic group by declared municipality, agency, exact normalized
subject and year. It must never be counted as a distinct physical incident.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import UTC, datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from tempfile import TemporaryDirectory
from unicodedata import combining, normalize
from uuid import NAMESPACE_URL, uuid5

import httpx

CKAN = 'https://dados.es.gov.br/api/3/action/'
DATASET = 'https://dados.es.gov.br/dataset/manifestacoes-da-ouvidoria'
RESOURCES = {
    2026: '46ddbf22-cc80-49f3-812a-ae7c6ac88d97',
    2025: 'edbe3888-9138-4174-b52f-52394ef025cb',
}
FIELDS = ('_id', 'Ano', 'TipoManifestacao', 'Orgao', 'Assunto', 'Municipio',
          'Situacao', 'DataRegistro', 'DataSituacao')
DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[1] / 'data/official/reported-problems-es.json.gz'
# Reviewed public vocabulary from the two official resources. Matching is exact,
# after case/accent/whitespace normalization; agencies are also explicit.
MAPPING_RULES = [
    ('sanitation', ('CESAN', 'ARSP', 'AGERH', 'SEDURB', 'SAAE ARACRUZ'), (
        'Vazamento de Água', 'Vazamento/Obstrução de Esgoto',
        'Abastecimento De Água', 'Falta de Água / Baixa Pressão no Abastecimento',
        'Obstrução de Rede de Esgoto', 'Rede De Esgoto',
        'Água com Cor / Cheiro / Gosto / Partículas', 'Cheiro Forte de Esgoto',
        'Água com Suspeita de Contaminação', 'Qualidade Da Água',
        'Saneamento Básico', 'Rede Hidráulica', 'Água Com Gosto Ruim',
        'Despejo Ou Descarte De Resíduos', 'Carro Pipa',
    )),
    ('mobility', ('CETURB', 'SEMOBI'), (
        'Transporte Público', 'Horários/Itinerários do transporte público',
        'Pontualidade/Atrasos do transporte público',
        'Recusa de embarque/desembarque (Sistema Transcol)',
        'Recusa de embarque/desembarque (Rodoviário Intermunicipal)',
        'Acessibilidade nos veículos de transporte público',
        'Manutenção dos Veículos de transporte público',
        'Sistema de Transporte Rodoviário Intermunicipal de Passageiros - SITRIP',
        'Superlotação em horários de pico', 'Falta de Fiscalização no transporte público',
        'Ponto de ônibus', 'Mobilidade Urbana', 'Terminal',
        'Limpeza e Higiene dos Veículos de transporte público',
        'Acessibilidade nos Terminais/Estações', 'Transporte + Acessível',
        'Criação/Alteração de ponto de parada', 'Criação de nova linha de ônibus',
        'Integração temporal entre modais do Sistema Transcol',
        'Infraestrutura dos Terminais/Estações',
        'Manutenção da sinalização de ponto de parada',
        'Limpeza e Higiene dos Terminais/Estações',
        'Infraestrutura na Terminal Rodoviário de Vitória', 'Infraestrutura da Ciclovia da Vida',
    )),
    ('education', ('SEDU',), (
        'Escola Pública Estadual', 'Educação', 'Escolas', 'Merenda Escolar',
        'Uniforme Escolar', 'Ensino Médio', 'Ano Letivo', 'Escola Viva',
        'Fiscalização de Transporte Escolar', 'Calendário Escolar',
        'Material Escolar', 'Material Educacional', 'Reposição De Aula',
        'Educação Profissional', 'Centros Estaduais de Idiomas (CEI)',
    )),
    ('health', ('SESA', 'INOVA'), (
        'Marcação De Exames E/Ou Consultas', 'Assistência À Saúde', 'Saúde Pública',
        'Farmácia Cidadã', 'Serviços de Saúde ofertados', 'Hospitais',
        'Medicamentos Na Rede Sus', 'Leitos Hospitalares',
        'Samu - Serviço De Atendimento Móvel De Urgência',
        'Vigilância Sanitária', 'Ambulâncias', 'Alimentação Hospitalar',
        'Material Hospitalar', 'Vacinação', 'Banco De Sangue',
        'Infraestrutura De Posto, Órgão Ou Unidade',
    )),
    ('infrastructure', ('DER', 'SEDURB', 'CESAN', 'SEMOBI', 'CETURB'), (
        'Buracos em via pública', 'Buraco no asfalto', 'Reparo de Pavimentação',
        'Estradas E Rodovias Do Es', 'Obras Em Estradas E Rodovias Do Es',
        'Manutenção De Estradas E Rodovias Do Es',
        'Sinalização De Estradas E Rodovias Do Es', 'Estradas e Pontes',
        'Obras Públicas', 'Obra inacabada', 'Iluminação Pública',
        'Infraestrutura da Rodovia do Sol',
    )),
    ('environment', ('IEMA', 'SEAMA', 'IDAF'), (
        'Meio Ambiente', 'Poluição Ambiental', 'Parque Ambiental',
        'Desastres Ambientais', 'Ar e Áreas Contaminadas',
        'Unidades de Conservação - Parque Ambiental', 'Proteção Ambiental',
        'Despejo Ou Descarte De Resíduos',
    )),
]


def _key(value) -> str:
    if not isinstance(value, str):
        return ''
    return ' '.join(''.join(c for c in normalize('NFKD', value) if not combining(c)).casefold().split())


_REVIEWED_PAIRS = {(_key(subject), agency): category
                   for category, agencies, subjects in MAPPING_RULES
                   for subject in subjects for agency in agencies}
_REVIEWED_SUBJECTS = {subject for subject, _ in _REVIEWED_PAIRS}



def _source(url: str, year: int, fetched_at: str) -> dict:
    return {
        'id': str(uuid5(NAMESPACE_URL, url)),
        'title': f'Manifestações da Ouvidoria {year} — SECONT/ES',
        'url': url, 'publisher': 'SECONT - Secretaria de Estado de Controle e Transparência',
        'source_type': 'official', 'published_at': None, 'checked_at': fetched_at,
    }


def _refresh_sources(existing: list, incoming: list) -> list:
    by_id = {source['id']: source for source in incoming}
    refreshed, seen = [], set()
    for source in existing:
        expected = by_id.get(source.get('id'))
        legacy = source.get('type') == 'official_reported_problems'
        if legacy:
            expected = next((s for s in incoming if s['url'] == source.get('url')), None)
        if expected:
            seen.add(expected['id'])
            # checked_at is refresh metadata; all documentary fields must still
            # equal our generated values before replacing a native entry.
            unedited = all(source.get(k) == v for k, v in expected.items() if k != 'checked_at')
            refreshed.append(expected if legacy or unedited else source)
        else:
            refreshed.append(source)
    refreshed.extend(source for source in incoming
                     if source['id'] not in seen
                     and not any(old.get('url') == source['url'] for old in existing))
    return refreshed


def _recorded_date(raw, fetched_day) -> tuple[str | None, str | None]:
    if raw in (None, ''):
        return None, None
    # Source timestamps are preserved verbatim when valid. A future day is a
    # quality problem, never a license to swap day/month or guess a timezone.
    if not isinstance(raw, str) or len(raw) > 40 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.+)?', raw):
        return None, 'malformed_date_rows'
    try:
        day = datetime.fromisoformat(raw).date()
    except ValueError:
        return None, 'malformed_date_rows'
    if day > fetched_day:
        return None, 'future_date_rows'
    return raw, None

def normalize_records(resource_rows: dict[str, list[dict]], catalog: dict,
                      fetched_at: str, resources: list[dict] | None = None) -> dict:
    """Keep only reviewed collective-service complaints and hash local source IDs."""
    codes = {_key(row['name']): str(row['code']) for row in catalog['municipalities']
             if row['state_abbreviation'] == 'ES'}
    rows, groups = {}, defaultdict(list)
    rejected, rejected_subjects = Counter(), Counter()
    types, agencies, subjects = Counter(), Counter(), Counter()
    total = 0
    date_quality = {'future_date_rows': 0, 'malformed_date_rows': 0}
    fetched_day = datetime.fromisoformat(fetched_at).date()
    for source_key, source_rows in resource_rows.items():
        if source_key not in RESOURCES.values():
            raise ValueError('Recurso oficial não cadastrado')
        expected_year = next(year for year, resource in RESOURCES.items() if resource == source_key)
        for row in source_rows:
            total += 1
            types[str(row.get('TipoManifestacao') or 'Não informado')] += 1
            reason = None
            subject = ' '.join(str(row.get('Assunto') or '').split())
            agency = ' '.join(str(row.get('Orgao') or '').split()).upper()
            if _key(row.get('TipoManifestacao')) != 'reclamacao':
                reason = 'not_complaint'
            elif str(row.get('Ano')) != str(expected_year):
                reason = 'unexpected_year'
            elif _key(row.get('Municipio')) not in codes:
                reason = 'unmapped_declared_municipality'
            else:
                agencies[agency] += 1
                subjects[subject] += 1
                category = _REVIEWED_PAIRS.get((_key(subject), agency))
                if _key(subject) not in _REVIEWED_SUBJECTS:
                    reason = 'unmapped_or_noncollective_subject'
                elif not category:
                    reason = 'unsupported_subject_agency'
                elif not isinstance(row.get('_id'), int) or row['_id'] < 1:
                    reason = 'missing_source_id'
                elif len(subject) > 200 or len(agency) > 160:
                    reason = 'invalid_public_label'
            if reason:
                rejected[reason] += 1
                if reason in {'unmapped_or_noncollective_subject', 'unsupported_subject_agency'}:
                    rejected_subjects[subject] += 1
                continue
            code = codes[_key(row['Municipio'])]
            group_key = f'{code}|{_key(agency)}|{_key(subject)}|{expected_year}'
            issue_id = str(uuid5(NAMESPACE_URL, f'{DATASET}|{group_key}'))
            record_id = hashlib.sha256(f'{source_key}|{row["_id"]}'.encode()).hexdigest()
            recorded_at, date_error = _recorded_date(row.get('DataRegistro'), fetched_day)
            if date_error:
                date_quality[date_error] += 1
            record = {
                'id': record_id, 'issue_id': issue_id, 'source_key': source_key,
                'year': expected_year, 'municipality_code': code, 'subject': subject,
                'agency': agency, 'manifestation_type': 'Reclamação',
                'processing_status': str(row.get('Situacao') or 'Não informado')[:80],
                'recorded_at': recorded_at,
                'source_url': f'{DATASET}/resource/{source_key}', 'fetched_at': fetched_at,
            }
            if record_id in rows:
                if rows[record_id] != record:
                    raise ValueError('Chave de origem duplicada com conteúdo divergente')
                rejected['duplicate_source_record'] += 1
                continue
            rows[record_id] = record
            groups[issue_id].append(record)
    names = {str(row['code']): row['name'] for row in catalog['municipalities']}
    issues = []
    for issue_id, records in sorted(groups.items()):
        record = records[0]
        dates = sorted(r['recorded_at'] for r in records if r['recorded_at'])
        year, subject, agency, code = (record[k] for k in ('year', 'subject', 'agency', 'municipality_code'))
        issues.append({
            'id': issue_id, 'title': f'Reclamações sobre {subject}'[:180],
            'summary': (
                'Reclamações registradas oficialmente na Ouvidoria do Espírito Santo '
                f'para {agency}, sobre {subject}, em {year}. Dossiê temático agrupado por assunto, '
                f'órgão, ano e município declarado ({names[code]}). O município informado na fonte '
                'não identifica o endereço do problema; estes registros não representam ocorrências '
                'físicas distintas geolocalizadas. A situação administrativa Encerrada não significa '
                'que o problema foi resolvido. A existência do registro oficial não comprova o conteúdo da reclamação.'
            ),
            'category': _REVIEWED_PAIRS[(_key(subject), agency)], 'municipality_code': code,
            'neighborhood': '', 'latitude': None, 'longitude': None, 'origin': 'official',
            'verification_status': 'official_registered', 'operational_status': 'not_assessed',
            'first_reported_at': dates[0] if dates else None,
            'last_activity_at': dates[-1] if dates else fetched_at,
            'is_demo': False,
            'sources': [_source(url, year, fetched_at)
                        for url in sorted({r['source_url'] for r in records})],
        })
    return {
        'schema_version': 1, 'fetched_at': fetched_at,
        'resources': resources if resources is not None else [
            {'id': key, 'year': next(y for y, r in RESOURCES.items() if r == key),
             'total_rows': len(value)} for key, value in sorted(resource_rows.items())
        ],
        'quality': {
            'total_rows': total, 'accepted_rows': len(rows), 'dossiers': len(issues),
            **date_quality,
            'rejected_rows': sum(rejected.values()), 'rejected_by_reason': dict(sorted(rejected.items())),
            'rejected_subject_counts': dict(sorted(rejected_subjects.items())),
            'source_manifestation_types': dict(sorted(types.items())),
            'complaint_agency_counts': dict(sorted(agencies.items())),
            'complaint_subject_counts': dict(sorted(subjects.items())),
            'records_by_municipality': dict(sorted(Counter(r['municipality_code'] for r in rows.values()).items())),
            'dossiers_by_municipality': dict(sorted(Counter(r['municipality_code'] for r in issues).items())),
            'records_by_category': dict(sorted(Counter(_REVIEWED_PAIRS[(_key(r['subject']), r['agency'])] for r in rows.values()).items())),
        },
        'issues': issues, 'records': sorted(rows.values(), key=lambda row: row['id']),
    }


def _get(client, action: str, params: dict) -> dict:
    for attempt in range(3):
        try:
            response = client.get(CKAN + action, params=params)
            response.raise_for_status()
            payload = response.json()
            if not payload.get('success'):
                raise ValueError('CKAN retornou erro')
            return payload['result']
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError):
            if attempt == 2:
                raise
            time.sleep(0.5 * 2**attempt)


def fetch_snapshot(catalog: dict, client=None) -> dict:
    """Request only allowlisted public columns, with complete deterministic pagination."""
    if client is None:
        with httpx.Client(timeout=90, follow_redirects=False,
                          headers={'User-Agent': 'Projeto-Invisivel/0.1 (public complaints ingestion)'}) as client:
            return fetch_snapshot(catalog, client)
    package = _get(client, 'package_show', {'id': 'manifestacoes-da-ouvidoria'})
    available = {r['id']: r for r in package['resources']}
    data, metadata = {}, []
    fetched_at = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    for year, resource_id in RESOURCES.items():
        resource = available[resource_id]
        if not resource.get('datastore_active') or str(year) not in resource['name']:
            raise ValueError('Metadados do recurso oficial divergentes')
        rows, total = [], None
        while total is None or len(rows) < total:
            page = _get(client, 'datastore_search', {
                'resource_id': resource_id, 'fields': ','.join(FIELDS),
                'limit': 5000, 'offset': len(rows), 'sort': '_id asc',
            })
            if page.get('total_was_estimated'):
                raise ValueError('Total estimado impede verificar completude')
            if total is not None and total != page['total']:
                raise ValueError('A fonte mudou durante a coleta; repetir a importação')
            total = page['total']
            records = [{field: r.get(field) for field in FIELDS} for r in page['records']]
            if not records and len(rows) != total:
                raise ValueError('Paginação incompleta na fonte oficial')
            rows.extend(records)
        if len(rows) != total or len({r['_id'] for r in rows}) != total:
            raise ValueError('Registros de origem incompletos ou duplicados')
        data[resource_id] = rows
        metadata.append({
            'id': resource_id, 'year': year, 'name': resource['name'], 'total_rows': total,
            'source_url': f'{DATASET}/resource/{resource_id}', 'last_modified': resource.get('last_modified'),
            'package_metadata_modified': package.get('metadata_modified'),
            'publisher': package['organization']['title'], 'license': package.get('license_title'),
            'fetched_at': fetched_at, 'requested_fields': list(FIELDS),
        })
    return normalize_records(data, catalog, fetched_at, metadata)


def import_snapshot(db, path: str | Path = DEFAULT_SNAPSHOT) -> dict:
    """Reconcile complete managed resources within the caller's transaction.

    Missing official records are removed; dossier rows and human history remain.
    Only an empty, untouched official dossier is hidden as source_removed.
    """
    from sqlalchemy import delete, select
    from app.models import Audit, IngestionJob, Issue, OfficialRecord, Report
    compressed = Path(path).read_bytes()
    digest = hashlib.sha256(compressed).hexdigest()
    latest = db.scalars(select(IngestionJob).where(
        IngestionJob.source == 'official_reported_problems', IngestionJob.status == 'completed',
    ).order_by(IngestionJob.created_at.desc())).first()
    if latest and latest.result.get('snapshot_sha256') == digest:
        return {**latest.result, 'skipped': True}
    snapshot = json.loads(gzip.decompress(compressed))
    if snapshot.get('schema_version') != 1:
        raise ValueError('Versão do snapshot oficial incompatível')
    managed = {resource['id'] for resource in snapshot['resources']}
    incoming = snapshot['issues']
    incoming_ids = {row['id'] for row in incoming}
    records = snapshot['records']
    record_ids = {row['id'] for row in records}
    if (not managed or not managed.issubset(RESOURCES.values())
            or any(row['source_key'] not in managed or row['issue_id'] not in incoming_ids for row in records)
            or len(record_ids) != len(records) or len(incoming_ids) != len(incoming)
            or snapshot['quality']['accepted_rows'] != len(records)
            or snapshot['quality']['dossiers'] != len(incoming)):
        raise ValueError('Snapshot oficial incompleto ou com recursos divergentes')
    previous_records = list(db.execute(select(OfficialRecord.id, OfficialRecord.issue_id).where(
        OfficialRecord.source_key.in_(managed))))
    affected_ids = incoming_ids | {record.issue_id for record in previous_records}
    current = {row.id: row for row in db.scalars(select(Issue).where(Issue.id.in_(affected_ids)))}
    result = {'snapshot_sha256': digest, 'issues_created': 0, 'issues_updated': 0,
              'records_upserted': len(records), 'records_removed': 0,
              'issues_source_removed': 0, 'issues_restored': 0, 'skipped': False}
    dates_by_issue = defaultdict(list)
    for record in records:
        if record['recorded_at']:
            dates_by_issue[record['issue_id']].append(record['recorded_at'])
    for row in incoming:
        if row['id'] not in current:
            db.add(Issue(**row))
            result['issues_created'] += 1
        else:
            issue = current[row['id']]
            # Civic/moderator states, text, coordinates, merge decisions and
            # version remain intact. Only source dates/metadata are refreshed.
            issue.sources = _refresh_sources(issue.sources, row['sources'])
            official_dates = dates_by_issue[issue.id]
            if official_dates:
                issue.first_reported_at = (min(issue.first_reported_at, min(official_dates))
                                           if issue.first_reported_at else min(official_dates))
                issue.last_activity_at = max(issue.last_activity_at, max(official_dates))
            if issue.origin == 'official' and issue.operational_status == 'source_removed':
                issue.operational_status = 'not_assessed'
                result['issues_restored'] += 1
                db.add(Audit(actor_id='official_reported_problems', action='official_source_restored',
                             target_id=issue.id, reason='Reclamações oficiais voltaram a integrar o recorte importado.'))
            result['issues_updated'] += 1
    db.flush()
    for start in range(0, len(records), 500):
        batch = records[start:start + 500]
        existing = {r.id: r for r in db.scalars(select(OfficialRecord).where(
            OfficialRecord.id.in_([r['id'] for r in batch])))}
        for row in batch:
            if row['id'] in existing:
                for key, value in row.items():
                    setattr(existing[row['id']], key, value)
            else:
                db.add(OfficialRecord(**row))
        db.flush()
    stale_ids = [record.id for record in previous_records if record.id not in record_ids]
    for start in range(0, len(stale_ids), 500):
        db.execute(delete(OfficialRecord).where(OfficialRecord.id.in_(stale_ids[start:start + 500])),
                   execution_options={'synchronize_session': 'fetch'})
    result['records_removed'] = len(stale_ids)
    db.flush()
    still_backed = set(db.scalars(select(OfficialRecord.issue_id).where(
        OfficialRecord.issue_id.in_(affected_ids)).distinct()))
    citizen_backed = set(db.scalars(select(Report.issue_id).where(
        Report.issue_id.in_(affected_ids), Report.moderation_status == 'approved').distinct()))
    for issue_id, issue in current.items():
        if (issue_id not in still_backed and issue_id not in citizen_backed
                and issue.origin == 'official' and issue.operational_status == 'not_assessed'
                and issue.verification_status == 'official_registered' and not issue.merged_into
                and issue.version == 1):
            issue.operational_status = 'source_removed'
            result['issues_source_removed'] += 1
            db.add(Audit(actor_id='official_reported_problems', action='official_source_removed',
                         target_id=issue.id,
                         reason='Nenhuma reclamação do recorte oficial atual permanece neste dossiê. '
                                'A retirada da fonte não comprova resolução; histórico e fontes documentais foram preservados.'))
    db.add(IngestionJob(source='official_reported_problems', status='completed', result=result))
    db.flush()
    return result


def sync_reported_problems(output=DEFAULT_SNAPSHOT, catalog=None, client=None) -> dict:
    """Collect first, then atomically replace each sanitized snapshot artifact."""
    output = Path(output)
    if catalog is None:
        catalog = output.parent / 'catalog.json'
    if not isinstance(catalog, dict):
        catalog = json.loads(Path(catalog).read_text(encoding='utf-8'))
    snapshot = fetch_snapshot(catalog, client=client)
    raw = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode()
    compressed = gzip.compress(raw, mtime=0)
    manifest = {
        'schema_version': 1, 'fetched_at': snapshot['fetched_at'], 'resources': snapshot['resources'],
        'quality': snapshot['quality'], 'file': output.name,
        'snapshot_sha256': hashlib.sha256(compressed).hexdigest(), 'bytes': len(compressed),
        'grouping': 'declared municipality + agency + exact normalized subject + year',
        'limitations': [
            'Dossiês temáticos não são ocorrências físicas distintas.',
            'Município declarado na fonte não é endereço do problema; não há coordenadas.',
            'Encerrada é situação administrativa e não comprova resolução.',
            'Registro oficial comprova recebimento da reclamação, não o conteúdo alegado.',
            'Apenas Reclamação; assuntos e órgãos precisam de mapeamento explícito para serviços coletivos.',
            'Não são coletados protocolo, nome, gênero ou narrativa.',
            'Datas futuras ou malformadas são tratadas como desconhecidas; não há reinterpretação de dia/mês ou fuso.',
            'Sem data de registro válida, first_reported_at é nulo; last_activity_at indica apenas a importação.',
        ],
        'mapping_rules': [{'category': c, 'agencies': list(a), 'subjects': list(s)} for c, a, s in MAPPING_RULES],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.parent / 'reported-problems-manifest.json'
    # Sibling temporary files stay on the same filesystem for atomic replace.
    # Collection and serialization must succeed before touching prior outputs.
    with TemporaryDirectory(dir=output.parent, prefix='.reported-problems-') as temporary:
        staged_snapshot = Path(temporary) / 'snapshot.json.gz'
        staged_manifest = Path(temporary) / 'manifest.json'
        staged_snapshot.write_bytes(compressed)
        staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        staged_snapshot.replace(output)
        staged_manifest.replace(manifest_path)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument('--catalog', type=Path, default=None)
    args = parser.parse_args()
    manifest = sync_reported_problems(args.output, args.catalog)
    print(json.dumps({k: manifest['quality'][k] for k in (
        'total_rows', 'accepted_rows', 'dossiers', 'rejected_by_reason',
        'records_by_municipality', 'dossiers_by_municipality', 'records_by_category')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
