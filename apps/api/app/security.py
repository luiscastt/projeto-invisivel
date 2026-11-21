import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from .db import get_db, now
from .models import User, AuthSession, Report, Vote, Evidence, Audit
from .schemas import Login, Register, DeleteAccount, Clarification

router = APIRouter(prefix="/auth", tags=["Autenticação"])
COOKIE = "invisivel_session"


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_password(password, stored):
    try:
        _, salt, digest = stored.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(digest, candidate)
    except (ValueError, TypeError):
        return False


def user_json(user):
    return {k: getattr(user, k) for k in ("id", "email", "display_name", "role")}


def optional_user(request: Request, db: Session = Depends(get_db, scope="function")):
    settings = request.app.state.settings
    bearer = request.headers.get("authorization", "")
    if bearer.startswith("Bearer ") and settings.auth_provider == "supabase":
        try:
            r = httpx.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers={"apikey": settings.supabase_anon_key, "Authorization": bearer}, timeout=10)
            r.raise_for_status()
            info = r.json()
            if not info.get("email_confirmed_at"):
                raise HTTPException(403, "Confirme seu e-mail para participar.")
            user = db.scalar(select(User).where(User.provider_id == info["id"]))
            if user is None:
                email = info["email"].lower()
                user = User(email=email, display_name=info.get("user_metadata", {}).get("display_name", "Cidadão")[:80], provider_id=info["id"], role="admin" if email in [x.strip().lower() for x in settings.admin_emails.split(",")] else "citizen")
                db.add(user)
                db.flush()
            elif not user.deleted:
                # Grants follow the current verified identity, never editable JWT metadata.
                user.email = info["email"].lower()
                user.role = "admin" if user.email in [x.strip().lower() for x in settings.admin_emails.split(",")] else "citizen"
            return None if user.deleted else user
        except httpx.HTTPStatusError:
            raise HTTPException(401, "Sessão expirada. Entre novamente.")
        except (httpx.HTTPError, KeyError, ValueError):
            raise HTTPException(503, "Serviço de autenticação indisponível.")
    token = request.cookies.get(COOKIE)
    if not token or settings.auth_provider != "local":
        return None
    session = db.get(AuthSession, hashlib.sha256(token.encode()).hexdigest())
    if session is None or session.expires_at <= now():
        return None
    user = db.get(User, session.user_id)
    return user if user and not user.deleted else None


def require_user(request: Request, user=Depends(optional_user), db: Session = Depends(get_db, scope="function")):
    if user is None:
        raise HTTPException(401, "Entre na sua conta para participar.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        user = db.scalar(select(User).where(User.id == user.id).with_for_update())
        if user is None or user.deleted:
            raise HTTPException(401, "Esta conta não está mais ativa.")
    return user


def require_admin(user=Depends(require_user)):
    if user.role != "admin":
        raise HTTPException(403, "Acesso restrito à equipe de moderação.")
    return user


def set_session(user, request, response, db):
    token = secrets.token_urlsafe(48)
    ttl = request.app.state.settings.session_days * 86400
    db.add(AuthSession(id=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires_at=(datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()))
    response.set_cookie(COOKIE, token, max_age=ttl, httponly=True, secure=request.app.state.settings.app_env == "production", samesite="lax", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"user": user_json(user)}


def local_only(request):
    if request.app.state.settings.auth_provider != "local":
        raise HTTPException(400, "Utilize o provedor de autenticação configurado.")


@router.get("/config")
def config(request: Request):
    s = request.app.state.settings
    local = s.app_env == "development" and s.auth_provider == "local"
    return {"provider": s.auth_provider, "supabase_url": s.supabase_url, "supabase_anon_key": s.supabase_anon_key, "local_test_accounts": local, "test_accounts": [{"email": email, "password": "Invisivel!2026", "display_name": name, "role": role} for email, name, role in [("cidadao@invisivel.local", "Cidadão de teste", "citizen"), ("admin@invisivel.local", "Equipe de moderação", "admin")]] if local else []}


@router.post("/register", status_code=201)
def register(body: Register, request: Request, response: Response, db: Session = Depends(get_db, scope="function")):
    local_only(request)
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "Este e-mail já está cadastrado.")
    user = User(email=body.email, display_name=body.display_name, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    return set_session(user, request, response, db)


@router.post("/login")
def login(body: Login, request: Request, response: Response, db: Session = Depends(get_db, scope="function")):
    local_only(request)
    user = db.scalar(select(User).where(User.email == body.email, User.deleted == False))
    if not verify_password(body.password, user.password_hash if user else "scrypt$dummy$" + "0" * 128):
        raise HTTPException(401, "E-mail ou senha incorretos.")
    return set_session(user, request, response, db)


@router.get("/me")
def me(user=Depends(require_user)):
    return user_json(user)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db, scope="function")):
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(AuthSession).where(AuthSession.id == hashlib.sha256(token.encode()).hexdigest()))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


account_router = APIRouter(prefix="/me", tags=["Minha conta"])


@account_router.get("/reports")
def my_reports(user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    return [{"id": r.id, "tracking_code": r.tracking_code, "title": r.payload["title"], "moderation_status": r.moderation_status, "reason": r.reason, "issue_id": r.issue_id, "created_at": r.created_at, "clarifications": r.payload.get("clarifications", [])} for r in db.scalars(select(Report).where(Report.author_id == user.id).order_by(Report.created_at.desc()))]


@account_router.post("/reports/{report_id}/reply", status_code=201)
def reply_to_moderation(report_id: str, body: Clarification, user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    report = db.scalar(select(Report).where(Report.id == report_id, Report.author_id == user.id).with_for_update())
    if report is None:
        raise HTTPException(404, "Relato não encontrado.")
    if report.moderation_status != "clarification_requested":
        raise HTTPException(409, "Este relato não aguarda esclarecimento.")
    replies = report.payload.get("clarifications", [])
    if len(replies) >= 10:
        raise HTTPException(422, "Limite de esclarecimentos atingido para este relato.")
    report.payload = {**report.payload, "clarifications": [*replies, {"description": body.description, "created_at": now()}]}
    report.moderation_status = "pending"
    db.add(Audit(actor_id=user.id, action="clarification_received", target_id=report.id, reason="Resposta privada do autor recebida; texto original preservado."))
    return {"ok": True}


@account_router.get("/export")
def export_data(user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    return {"account": user_json(user), "reports": [{"id": r.id, "original": r.payload, "moderation_status": r.moderation_status, "created_at": r.created_at} for r in db.scalars(select(Report).where(Report.author_id == user.id))], "votes": [{"issue_id": v.issue_id, "vote": v.vote} for v in db.scalars(select(Vote).where(Vote.user_id == user.id))]}


@account_router.delete("")
def delete_account(body: DeleteAccount, request: Request, response: Response, user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    if user.role == "admin":
        raise HTTPException(400, "Transfira a administração antes de excluir esta conta.")
    if request.app.state.settings.auth_provider == "local" and not verify_password(body.password or "", user.password_hash):
        raise HTTPException(403, "Confirme a senha para excluir a conta.")
    db.execute(delete(Vote).where(Vote.user_id == user.id))
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    for report in db.scalars(select(Report).where(Report.author_id == user.id).with_for_update()):
        if report.moderation_status != "approved":
            report.payload = {"title": "Relato removido pelo autor", "description": "Conteúdo removido a pedido do autor.", "anonymous": True}
            report.moderation_status = "rejected"
            report.flags = []
            report.reason = "Conteúdo privado removido a pedido do titular."
    remove_paths = []
    for evidence in db.scalars(select(Evidence).where(Evidence.owner_id == user.id, Evidence.approved == False)):
        remove_paths.append(request.app.state.settings.data_dir / evidence.path)
        db.delete(evidence)
    user.email = f"deleted-{user.id}@invalid.local"
    user.display_name = "Conta excluída"
    user.password_hash = ""
    user.deleted = True
    db.add(Audit(actor_id=user.id, action="account_deleted", target_id=user.id, reason="Solicitação do titular; contribuições públicas preservadas de forma pseudonimizada."))
    db.commit()
    # Files are only removed after durable DB deletion. A disk failure leaves an inaccessible orphan.
    import logging
    for path in remove_paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logging.getLogger("invisivel").warning("Arquivo órfão pendente de limpeza: %s", path.name)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True, "note": "Dados da aplicação removidos/pseudonimizados. Se usou Supabase, solicite também a exclusão da identidade ao operador."}
