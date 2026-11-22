from datetime import datetime, timezone
from uuid import uuid4
import re
from sqlalchemy import create_engine, event, text, inspect
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
        options["execution_options"] = {"schema_translate_map": {None: schema}}
        options["connect_args"] = {"prepare_threshold": None, "connect_timeout": 15}
    engine = create_engine(url, **options)
    if engine.dialect.name == "postgresql":
        @event.listens_for(engine, "begin")
        def select_application_schema(connection):
            # Poolers may ignore startup options. Scope every transaction explicitly.
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')
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


def _upgrade_sqlite_issues(engine):
    from sqlalchemy.schema import CreateTable
    from .models import Issue
    with engine.connect() as connection:
        inspector = inspect(connection)
        if not inspector.has_table("issues"):
            return
        columns = inspector.get_columns("issues")
        names = {c["name"] for c in columns}
        if "origin" in names and all(c["nullable"] for c in columns if c["name"] in {"latitude", "longitude", "first_reported_at"}):
            return
        if names - set(Issue.__table__.columns.keys()):
            raise RuntimeError("Schema SQLite não reconhecido; preserve o arquivo e revise a migração.")
        connection.commit()
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        try:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            ddl = str(CreateTable(Issue.__table__).compile(engine)).replace("CREATE TABLE issues (", "CREATE TABLE issues_replacement (", 1)
            connection.exec_driver_sql(ddl)
            fields = ", ".join('"' + c["name"] + '"' for c in columns)
            connection.exec_driver_sql(f"INSERT INTO issues_replacement ({fields}) SELECT {fields} FROM issues")
            connection.exec_driver_sql("DROP TABLE issues")
            connection.exec_driver_sql("ALTER TABLE issues_replacement RENAME TO issues")
            for index in Issue.__table__.indexes:
                index.create(connection, checkfirst=True)
            if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchone():
                raise RuntimeError("Migração cancelada: referência SQLite inconsistente.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


def initialize_database(engine, settings):
    """Provision application tables atomically; PostgreSQL clients never receive direct grants."""
    from .seed import bootstrap
    if engine.dialect.name == "sqlite":
        _upgrade_sqlite_issues(engine)
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(734188219)"))
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}"'))
        Base.metadata.create_all(connection)
        if engine.dialect.name == "postgresql":
            columns = {c["name"]: c for c in inspect(connection).get_columns("issues", schema=settings.database_schema)}
            target = f'"{settings.database_schema}"."issues"'
            if "origin" not in columns:
                connection.execute(text(f"ALTER TABLE {target} ADD COLUMN origin VARCHAR(24) NOT NULL DEFAULT 'community'"))
            for name in ("latitude", "longitude", "first_reported_at"):
                if not columns[name]["nullable"]:
                    connection.execute(text(f'ALTER TABLE {target} ALTER COLUMN "{name}" DROP NOT NULL'))
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
            snapshot = settings.official_dir / "reported-problems-es.json.gz"
            if snapshot.is_file():
                from pipelines.reported_problems import import_snapshot
                import_snapshot(db, snapshot)
            db.flush()
