from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from .db import get_db, now, uid
from .models import Issue, Report, Vote, Evidence, Update, User
from .security import optional_user, require_user
from .schemas import ReportInput, VoteInput
from .territories import municipality, validate_location
from .algorithms import similarity, detect_flags, normalize

router = APIRouter(tags=["Problemas e participação"])


def get_issue(db, id_, lock=False):
    query = select(Issue).where(Issue.id == id_)
    if lock:
        query = query.with_for_update()
    issue = db.scalar(query)
    if issue is None:
        raise HTTPException(404, "Problema não encontrado.")
    return issue


def vote_counts(db, issue_id, user=None):
    counts = dict(db.execute(select(Vote.vote, func.count()).where(Vote.issue_id == issue_id).group_by(Vote.vote)).all())
    mine = db.scalar(select(Vote.vote).where(Vote.issue_id == issue_id, Vote.user_id == user.id)) if user else None
    return {"resolved": counts.get("RESOLVED", 0), "unresolved": counts.get("UNRESOLVED", 0), "my_vote": mine}


def issue_json(db, issue, request, user=None):
    m = municipality(request, issue.municipality_code)
    result = {k: getattr(issue, k) for k in ("id", "title", "summary", "category", "municipality_code", "neighborhood", "latitude", "longitude", "verification_status", "operational_status", "first_reported_at", "last_activity_at", "is_demo", "version")}
    result.update(municipality_name=m["name"], state_abbreviation=m["state_abbreviation"])
    result["reports_count"] = db.scalar(select(func.count()).select_from(Report).where(Report.issue_id == issue.id, Report.moderation_status == "approved")) or 0
    result["evidence_count"] = db.scalar(select(func.count()).select_from(Evidence).where(Evidence.issue_id == issue.id, Evidence.approved == True)) or 0
    result["votes"] = vote_counts(db, issue.id, user)
    # No invented severity, affected population or neighborhood vulnerability.
    result["priority"] = {"score": None, "reason": "Sem avaliação: gravidade, população potencialmente afetada e vulnerabilidade local ainda não foram verificadas. Ordenação por data ou relatos é descritiva."}
    return result


def evidence_json(e):
    return {"id": e.id, "url": f"/api/v1/media/{e.id}", "caption": e.caption, "verification_status": e.verification_status}


def issue_detail(db, issue, request, user=None):
    result = issue_json(db, issue, request, user)
    reports = list(db.scalars(select(Report).where(Report.issue_id == issue.id, Report.moderation_status == "approved").order_by(Report.created_at)))
    result["reports"] = [{"id": r.id, "description": r.payload["description"], "display_name": "Relato sem identificação pública" if r.payload.get("anonymous", True) or db.get(User, r.author_id).deleted else (db.get(User, r.author_id).display_name), "created_at": r.created_at, "contribution_type": r.contribution_type} for r in reports]
    result["sources"] = issue.sources
    result["updates"] = [{k: getattr(u, k) for k in ("id", "version", "update_type", "description", "created_at", "reason")} for u in db.scalars(select(Update).where(Update.issue_id == issue.id).order_by(Update.version))]
    result["evidence"] = [evidence_json(e) for e in db.scalars(select(Evidence).where(Evidence.issue_id == issue.id, Evidence.approved == True))]
    return result


def find_duplicates(db, body, request, user=None):
    values = body.model_dump(mode="json")
    values["created_at"] = now()
    result = []
    for issue in db.scalars(select(Issue).where(Issue.municipality_code == body.municipality_code, Issue.is_demo == body.is_demo, Issue.merged_into.is_(None))):
        other = {**issue_json(db, issue, request, user), "created_at": issue.last_activity_at}
        score = similarity(values, other)
        if score["score"] >= .65:
            result.append({"issue": other, **score})
    return sorted(result, key=lambda r: (-r["score"], r["issue"]["id"]))[:5]


@router.get("/issues")
def list_issues(request: Request, municipality: str | None = None, state: str | None = None, neighborhood: str | None = None, category: str | None = None, operational_status: str | None = None, verification_status: str | None = None, search: str = "", bbox: str | None = None, demo: bool = False, sort: str = "recent", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db, scope="function"), user=Depends(optional_user)):
    query = select(Issue).where(Issue.is_demo == demo, Issue.merged_into.is_(None))
    if municipality:
        query = query.where(Issue.municipality_code == municipality)
    if state:
        query = query.where(Issue.municipality_code.startswith(state))
    for column, value in [(Issue.neighborhood, neighborhood), (Issue.category, category), (Issue.operational_status, operational_status), (Issue.verification_status, verification_status)]:
        if value:
            query = query.where(column == value)
    if bbox:
        try:
            west, south, east, north = map(float, bbox.split(","))
            if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                raise ValueError()
        except ValueError:
            raise HTTPException(422, "bbox deve conter oeste,sul,leste,norte válidos.")
        query = query.where(Issue.longitude.between(west, east), Issue.latitude.between(south, north))
    values = [issue_json(db, i, request, user) for i in db.scalars(query)]
    if search:
        needle = normalize(search)
        values = [i for i in values if needle in normalize(i["title"] + " " + i["summary"] + " " + i["neighborhood"])]
    if sort == "unresolved":
        values = [i for i in values if i["operational_status"] != "verified_resolved"]
    if sort == "reports":
        values.sort(key=lambda i: (-i["reports_count"], i["id"]))
    else:
        values.sort(key=lambda i: (i["last_activity_at"], i["id"]), reverse=True)
    return {"items": values[(page - 1) * page_size:page * page_size], "total": len(values), "page": page, "page_size": page_size}


@router.get("/issues/{issue_id}")
def detail(issue_id: str, request: Request, db: Session = Depends(get_db, scope="function"), user=Depends(optional_user)):
    issue = get_issue(db, issue_id)
    if issue.merged_into:
        return RedirectResponse(f"/api/v1/issues/{issue.merged_into}")
    return issue_detail(db, issue, request, user)


@router.get("/issues/{issue_id}/{section}")
def get_section(issue_id: str, section: str, request: Request, db: Session = Depends(get_db, scope="function"), user=Depends(optional_user)):
    if section not in {"reports", "sources", "updates", "votes"}:
        raise HTTPException(404, "Seção não encontrada.")
    return issue_detail(db, get_issue(db, issue_id), request, user)[section]


@router.post("/issues/{issue_id}/votes")
def cast_vote(issue_id: str, body: VoteInput, user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    issue = get_issue(db, issue_id, lock=True)
    if issue.merged_into:
        raise HTTPException(409, "Este problema foi unificado. Abra o dossiê atualizado.")
    vote = db.scalar(select(Vote).where(Vote.issue_id == issue_id, Vote.user_id == user.id))
    if vote:
        vote.vote = body.vote
        vote.updated_at = now()
    else:
        db.add(Vote(issue_id=issue_id, user_id=user.id, vote=body.vote))
    db.flush()
    return vote_counts(db, issue_id, user)


@router.delete("/issues/{issue_id}/votes")
def remove_vote(issue_id: str, user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    get_issue(db, issue_id, lock=True)
    db.execute(delete(Vote).where(Vote.user_id == user.id, Vote.issue_id == issue_id))
    db.flush()
    return vote_counts(db, issue_id, user)


@router.post("/reports/check-duplicates")
def check_duplicates(body: ReportInput, request: Request, db: Session = Depends(get_db, scope="function"), user=Depends(require_user)):
    validate_location(request, body)
    return find_duplicates(db, body, request, user)


@router.post("/reports", status_code=201)
def submit_report(body: ReportInput, request: Request, db: Session = Depends(get_db, scope="function"), user=Depends(require_user)):
    validate_location(request, body)
    if body.existing_issue_id:
        issue = get_issue(db, body.existing_issue_id)
        if issue.merged_into or issue.municipality_code != body.municipality_code or issue.is_demo != body.is_demo:
            raise HTTPException(422, "Vinculação incompatível com o município ou modo selecionado.")
    if len(set(body.evidence_ids)) != len(body.evidence_ids):
        raise HTTPException(422, "Há evidências repetidas.")
    evidence = []
    for id_ in sorted(body.evidence_ids):
        item = db.scalar(select(Evidence).where(Evidence.id == id_).with_for_update())
        if item is None or item.owner_id != user.id or item.report_id is not None:
            raise HTTPException(422, "Evidência indisponível ou não pertence à sua conta.")
        evidence.append(item)
    flags = detect_flags(body.title + " " + body.description)
    if not request.app.state.settings.official_dir.joinpath(f"geometry-{body.municipality_code}.json").exists():
        flags.append("location_boundary_unavailable")
    report = Report(author_id=user.id, payload=body.model_dump(mode="json"), tracking_code="INV-" + uid().split("-")[0].upper(), flags=flags)
    db.add(report)
    db.flush()
    for e in evidence:
        e.report_id = report.id
    return {"id": report.id, "tracking_code": report.tracking_code, "moderation_status": report.moderation_status, "flags": flags}
