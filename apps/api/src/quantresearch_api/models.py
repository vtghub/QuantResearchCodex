from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


def uuid_string() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class TenantMixin:
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(40), default="active")


class Dataset(Base, TenantMixin, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(180))
    provider: Mapped[str] = mapped_column(String(80))
    asset_class: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="draft")
    checksum: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)


class ResearchRun(Base, TenantMixin, TimestampMixin):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True)
    parameters_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)


class Strategy(Base, TenantMixin, TimestampMixin):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(180))
    version: Mapped[str] = mapped_column(String(80), default="0.1.0")
    lifecycle: Mapped[str] = mapped_column(String(64), default="draft")
    approval_mode: Mapped[str] = mapped_column(String(64), default="two-person")
    artifact_uri: Mapped[str | None] = mapped_column(String(512))
    parameters_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True)
    actor: Mapped[str] = mapped_column(String(180))
    action: Mapped[str] = mapped_column(String(120))
    target_kind: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    payload_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
