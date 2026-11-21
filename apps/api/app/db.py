from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session
from fastapi import Request


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


def make_engine(url):
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}, pool_pre_ping=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
    return engine


def get_db(request: Request):
    with Session(request.app.state.engine) as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
