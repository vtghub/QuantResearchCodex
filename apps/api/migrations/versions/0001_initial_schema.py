"""Initial tenant-aware platform schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def tenant_columns() -> list[sa.Column]:
    return [
        sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True, index=True),
    ]


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        *tenant_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("asset_class", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "research_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        *tenant_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        *tenant_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("lifecycle", sa.String(length=64), nullable=False),
        sa.Column("approval_mode", sa.String(length=64), nullable=False),
        sa.Column("artifact_uri", sa.String(length=512), nullable=True),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "audit_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        *tenant_columns(),
        sa.Column("actor", sa.String(length=180), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_kind", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_records")
    op.drop_table("strategies")
    op.drop_table("research_runs")
    op.drop_table("datasets")
    op.drop_table("users")
    op.drop_table("workspaces")
    op.drop_table("organizations")
