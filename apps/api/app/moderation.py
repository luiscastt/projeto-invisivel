from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from .db import get_db, now, uid
from .models import Issue, Report, Evidence, Update, Audit, Vote, User, IngestionJob
from .security import require_admin
from .schemas import Approval, Reason, StatusInput, Restore, Merge, ReportInput
from .issues import get_issue, issue_json, find_duplicates, evidence_json
from .territories import municipality

router = APIRouter(prefix="/admin", tags=["Moderação"])
SNAPSHOT_FIELDS = ("title", "summary", "category", "verification_status", "operational_status", "sources", "neighborhood", "latitude", "longitude")


def record_update(db, issue, actor_id, update_type, reason, description, report_id=None, initial=False):
    if not initial:
        issue.version += 1
    issue.last_activity_at = now()
    db.add(Update(issue_id=issue.id, version=issue.version, update_type=update_type, description=description, reason=reason, snapshot={k: getattr(issue, k) for k in SNAPSHOT_FIELDS}, approved_by=actor_id, source_report_id=report_id))
    db.add(Audit(actor_id=actor_id, action=update_type, target_id=issue.id, reason=reason))
    db.flush()


def pending_report(db, report_id):
    author_id = db.scalar(select(Report.author_id).where(Report.id == report_id))
    if author_id:
        db.scalar(select(User).where(User.id == author_id).with_for_update())
    report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
    if report is None:
        raise HTTPException(404, "Relato não encontrado.")
    if report.moderation_status not in ("pending", "clarification_requested"):
        raise HTTPException(409, "Este relato já foi moderado.")
    return report


@router.get("/moderation")
def queue(request: Request, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    result = []
    for r in db.scalars(select(Report).where(Report.moderation_status.in_(["pending", "clarification_requested"])).order_by(Report.created_at)):
        item = {**r.payload, "id": r.id, "tracking_code": r.tracking_code, "created_at": r.created_at, "moderation_status": r.moderation_status, "flags": r.flags, "municipality_name": municipality(request, r.payload["municipality_code"])["name"], "reason": r.reason}
        item["evidence"] = [evidence_json(e) for e in db.scalars(select(Evidence).where(Evidence.report_id == r.id))]
        item["duplicates"] = find_duplicates(db, ReportInput.model_validate({k: v for k, v in r.payload.items() if k in ReportInput.model_fields}), request, admin)
        result.append(item)
    return result


@router.post("/reports/{report_id}/approve")
def approve(report_id: str, body: Approval, request: Request, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    report = pending_report(db, report_id)
    p = report.payload
    target_id = body.issue_id if "issue_id" in body.model_fields_set else p.get("existing_issue_id")
    if target_id:
        issue = get_issue(db, target_id, lock=True)
        if issue.municipality_code != p["municipality_code"] or issue.is_demo != p["is_demo"] or issue.merged_into:
            raise HTTPException(422, "O problema de destino não corresponde ao município ou ao modo do relato.")
        existing_texts = [r.payload["description"] for r in db.scalars(select(Report).where(Report.issue_id == issue.id, Report.moderation_status == "approved"))]
        is_new = p["description"] not in existing_texts
        report.contribution_type = "descriptive_complement" if is_new else "repeated_information"
        if is_new:
            issue.summary += "\n\nComplemento comunitário revisado:\n" + p["description"]
        initial = False
    else:
        issue = Issue(title=p["title"], summary=p["description"], category=p["category"], municipality_code=p["municipality_code"], neighborhood=p["neighborhood"], latitude=p["latitude"], longitude=p["longitude"], is_demo=p["is_demo"], sources=[])
        db.add(issue)
        db.flush()
        initial = True
    report.issue_id = issue.id
    report.moderation_status = "approved"
    report.reason = body.reason
    # Approval publishes sources as reviewed references, not corroboration of the allegation.
    known = {s["url"] for s in issue.sources}
    issue.sources = [*issue.sources, *[{**s, "id": uid(), "checked_at": now(), "review_status": "reviewed"} for s in p["sources"] if s["url"] not in known]]
    for e in db.scalars(select(Evidence).where(Evidence.report_id == report.id)):
        e.issue_id = issue.id
        e.approved = True
    record_update(db, issue, admin.id, "published" if initial else "contribution_approved", body.reason, "Primeiro relato publicado após revisão humana." if initial else "Contribuição comunitária revisada e associada ao dossiê; texto original preservado.", report.id, initial)
    return {"issue_id": issue.id}


@router.post("/reports/{report_id}/reject")
def reject(report_id: str, body: Reason, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    report = pending_report(db, report_id)
    report.moderation_status = "rejected"
    report.reason = body.reason
    db.add(Audit(actor_id=admin.id, action="report_rejected", target_id=report.id, reason=body.reason))
    return {"ok": True}


@router.post("/reports/{report_id}/clarify")
def clarify(report_id: str, body: Reason, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    report = pending_report(db, report_id)
    report.moderation_status = "clarification_requested"
    report.reason = body.reason
    db.add(Audit(actor_id=admin.id, action="clarification_requested", target_id=report.id, reason=body.reason))
    return {"ok": True}


@router.post("/issues/{issue_id}/status")
def change_status(issue_id: str, body: StatusInput, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    issue = get_issue(db, issue_id, lock=True)
    if issue.merged_into:
        raise HTTPException(409, "Problema unificado. Atualize o dossiê de destino.")
    if body.status == "verified_resolved" and not db.scalar(select(func.count()).select_from(Evidence).where(Evidence.issue_id == issue.id, Evidence.approved == True)) and not issue.sources:
        raise HTTPException(422, "Resolução verificada exige evidência ou fonte revisada no dossiê, além da justificativa.")
    old = issue.operational_status
    issue.operational_status = body.status
    record_update(db, issue, admin.id, "status_changed", body.reason, f"Acompanhamento alterado de {old} para {body.status}. Votos comunitários preservados separadamente.")
    return {"ok": True}


@router.post("/issues/{issue_id}/restore")
def restore(issue_id: str, body: Restore, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    issue = get_issue(db, issue_id, lock=True)
    old = db.scalar(select(Update).where(Update.issue_id == issue_id, Update.version == body.version))
    if not old or issue.merged_into:
        raise HTTPException(404, "Versão restaurável não encontrada.")
    for k, v in old.snapshot.items():
        if k in SNAPSHOT_FIELDS:
            setattr(issue, k, v)
    record_update(db, issue, admin.id, "version_restored", body.reason, f"Conteúdo da versão {body.version} restaurado em nova versão. Relatos e histórico preservados.")
    return {"ok": True}


@router.post("/issues/{issue_id}/merge")
def merge(issue_id: str, body: Merge, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    if issue_id == body.target_id:
        raise HTTPException(422, "Selecione outro problema de destino.")
    # Stable lock ordering avoids deadlock in PostgreSQL.
    ordered = {id_: get_issue(db, id_, lock=True) for id_ in sorted([issue_id, body.target_id])}
    source, target = ordered[issue_id], ordered[body.target_id]
    if source.merged_into or target.merged_into or source.municipality_code != target.municipality_code or source.is_demo != target.is_demo:
        raise HTTPException(422, "Problemas incompatíveis para unificação.")
    for r in db.scalars(select(Report).where(Report.issue_id == source.id)):
        r.issue_id = target.id
    for e in db.scalars(select(Evidence).where(Evidence.issue_id == source.id)):
        e.issue_id = target.id
    for vote in db.scalars(select(Vote).where(Vote.issue_id == source.id)):
        existing = db.scalar(select(Vote).where(Vote.issue_id == target.id, Vote.user_id == vote.user_id))
        if existing:
            db.delete(vote)
        else:
            vote.issue_id = target.id
    target.summary += "\n\nRegistro unificado após revisão:\n" + source.summary
    known = {s["url"] for s in target.sources}
    target.sources = [*target.sources, *[s for s in source.sources if s["url"] not in known]]
    source.merged_into = target.id
    record_update(db, source, admin.id, "merged", body.reason, f"Registro unificado ao dossiê {target.id}; URL original preservada por redirecionamento.")
    record_update(db, target, admin.id, "merge_received", body.reason, f"Recebeu relatos do dossiê {source.id}; votos duplicados não somados.")
    return {"ok": True, "issue_id": target.id}


@router.get("/audit")
def audit(admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    return [{k: getattr(a, k) for k in ("id", "actor_id", "action", "target_id", "reason", "created_at")} for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(200))]


@router.post("/evidence/{evidence_id}/withdraw")
def withdraw_evidence(evidence_id: str, body: Reason, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    evidence = db.scalar(select(Evidence).where(Evidence.id == evidence_id).with_for_update())
    if evidence is None or not evidence.approved or not evidence.issue_id:
        raise HTTPException(404, "Evidência publicada não encontrada.")
    issue = get_issue(db, evidence.issue_id, lock=True)
    evidence.approved = False
    record_update(db, issue, admin.id, "evidence_withdrawn", body.reason, "Uma evidência foi retirada da visualização pública após revisão. O histórico da decisão foi preservado.")
    return {"ok": True}


@router.get("/metrics")
def metrics(admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    return {"users": db.scalar(select(func.count()).select_from(User).where(User.deleted == False)), "issues": db.scalar(select(func.count()).select_from(Issue).where(Issue.is_demo == False, Issue.merged_into.is_(None))), "reports": db.scalar(select(func.count()).select_from(Report)), "pending": db.scalar(select(func.count()).select_from(Report).where(Report.moderation_status == "pending")), "votes": db.scalar(select(func.count()).select_from(Vote)), "ingestion_jobs": [{"id": j.id, "source": j.source, "status": j.status, "result": j.result, "created_at": j.created_at} for j in db.scalars(select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(10))]}


@router.post("/sync")
def sync(request: Request, admin=Depends(require_admin), db: Session = Depends(get_db, scope="function")):
    from pipelines.sync import run_sync
    from pipelines.public_services import sync_services
    from pipelines.es_sync import sync_es
    output = request.app.state.settings.official_dir
    core = run_sync(output)
    services = sync_services(output, transparency_key=request.app.state.settings.portal_transparencia_api_key)
    state_data = sync_es(output)
    result = {"core": core, "services": services, "state_data": state_data, "errors": [*core.get("errors", []), *services.get("errors", []), *state_data.get("errors", [])]}
    job = IngestionJob(source="official_public_apis", status="completed" if not result.get("errors") else "partial", result=result)
    db.add(job)
    db.add(Audit(actor_id=admin.id, action="official_sync", target_id="sources", reason="Sincronização de APIs públicas oficiais solicitada pela equipe."))
    return result
