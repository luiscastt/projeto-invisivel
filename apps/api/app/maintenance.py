"""Explicit retention job. Run daily with the operator's scheduler."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from .config import Settings
from .db import make_engine, now
from .models import Evidence, Report, AuthSession


def cleanup(settings=None):
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    paths = []
    with Session(engine) as db:
        day = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        month = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        for e in db.scalars(select(Evidence).where(Evidence.approved == False)):
            report = db.get(Report, e.report_id) if e.report_id else None
            if (report is None and e.created_at < day) or (report and report.moderation_status == "rejected" and e.created_at < month):
                paths.append(settings.data_dir / e.path)
                db.delete(e)
        db.execute(delete(AuthSession).where(AuthSession.expires_at < now()))
        db.commit()
    removed = 0
    for p in paths:
        p.unlink(missing_ok=True)
        removed += 1
    engine.dispose()
    return {"private_files_removed": removed}


if __name__ == "__main__":
    import json
    print(json.dumps(cleanup()))
