from sqlalchemy import String, Text, Float, Boolean, JSON, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, uid, now


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(20), default="citizen")
    provider_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[str] = mapped_column(String(40))


class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(180))
    summary: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), index=True)
    municipality_code: Mapped[str] = mapped_column(String(7), index=True)
    neighborhood: Mapped[str] = mapped_column(String(160), default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    verification_status: Mapped[str] = mapped_column(String(40), default="community_report")
    operational_status: Mapped[str] = mapped_column(String(40), default="reported", index=True)
    first_reported_at: Mapped[str] = mapped_column(String(40), default=now)
    last_activity_at: Mapped[str] = mapped_column(String(40), default=now)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    merged_into: Mapped[str | None] = mapped_column(ForeignKey("issues.id"), nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    tracking_code: Mapped[str] = mapped_column(String(32), unique=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    moderation_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    flags: Mapped[list] = mapped_column(JSON, default=list)
    reason: Mapped[str] = mapped_column(Text, default="")
    contribution_type: Mapped[str] = mapped_column(String(40), default="new_report")
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class Evidence(Base):
    __tablename__ = "issue_evidence"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), nullable=True)
    issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id"), nullable=True, index=True)
    path: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(String(300), default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(40), default="community_evidence")
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class Vote(Base):
    __tablename__ = "issue_votes"
    __table_args__ = (UniqueConstraint("issue_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id"), index=True)
    vote: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    updated_at: Mapped[str] = mapped_column(String(40), default=now)


class Update(Base):
    __tablename__ = "issue_updates"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    update_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict] = mapped_column(JSON)
    approved_by: Mapped[str] = mapped_column(String(64))
    source_report_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    __table_args__ = (UniqueConstraint("issue_id", "version"),)


class Audit(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(60))
    target_id: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class Simulation(Base):
    __tablename__ = "simulation_scenarios"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    source: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
