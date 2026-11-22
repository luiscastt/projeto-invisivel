from datetime import datetime, timezone
from uuid import uuid4
import re
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase, Session
from fastapi import Request


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


def make_engine(url, schema="public"):
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
        raise ValueError("Nome de schema inválido.")
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    else:
        options["poolclass"] = NullPool
        options["connect_args"] = {"options": f"-csearch_path={schema},public", "prepare_threshold": None, "connect_timeout": 15}
    engine = create_engine(url, **options)
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


def initialize_database(engine, settings):
    """Provision application tables atomically; PostgreSQL clients never receive direct grants."""
    from .seed import bootstrap
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(734188219)"))
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}"'))
        Base.metadata.create_all(connection)
        if engine.dialect.name == "postgresql":
            schema = settings.database_schema
            if schema != "public":
                connection.execute(text(f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC, anon, authenticated'))
            for table in Base.metadata.sorted_tables:
                target = f'"{schema}"."{table.name}"'
                connection.execute(text(f'ALTER TABLE {target} ENABLE ROW LEVEL SECURITY'))
                connection.execute(text(f'REVOKE ALL ON TABLE {target} FROM PUBLIC, anon, authenticated'))
        with Session(bind=connection) as db:
            bootstrap(db, settings)
            db.flush()
