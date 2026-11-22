"""Explicit retention job. Run daily with the operator's scheduler."""
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from .config import Settings
from .db import make_engine, now
from .models import Evidence, Report, AuthSession, StorageDeletion
from .storage import delete_evidence


def cleanup(settings=None):
    settings = settings or Settings()
    engine = make_engine(settings.database_url, schema=settings.database_schema)
    removed = 0
    try:
        with Session(engine) as db:
            day = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            month = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for e in db.scalars(select(Evidence).where(Evidence.approved == False)):
                report = db.get(Report, e.report_id) if e.report_id else None
                if (report is None and e.created_at < day) or (report and report.moderation_status == "rejected" and e.created_at < month):
                    db.add(StorageDeletion(path=e.path))
                    db.delete(e)
            db.execute(delete(AuthSession).where(AuthSession.expires_at < now()))
            db.commit()
            for pending in db.scalars(select(StorageDeletion)):
                try:
                    delete_evidence(settings, pending.path)
                except (HTTPException, OSError):
                    logging.getLogger("invisivel").warning("Arquivo órfão pendente de nova tentativa de limpeza.")
                else:
                    db.delete(pending)
                    removed += 1
            db.commit()
    finally:
        engine.dispose()
    return {"private_files_removed": removed}


if __name__ == "__main__":
    import json
    print(json.dumps(cleanup()))
