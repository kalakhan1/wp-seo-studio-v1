"""Initial schema: connections, drafts, publish_history, audit_reports,
prompt_templates, media_records, job_logs, app_settings.

Revision ID: 0001_init
Revises:
Create Date: 2026-10-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- connections -------------------------------------------------------
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("username", sa.String(length=200), nullable=False, server_default=""),
        sa.Column(
            "auth_method",
            sa.String(length=40),
            nullable=False,
            server_default="application_password",
        ),
        sa.Column("secret_ref", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("require_https", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_verified_ok",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_connections"),
        sa.UniqueConstraint("label", name="uq_connections_label"),
    )

    # --- drafts ------------------------------------------------------------
    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("slug", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("wp_object_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_drafts"),
    )
    op.create_index("ix_drafts_object_type", "drafts", ["object_type"])
    op.create_index("ix_drafts_connection_id", "drafts", ["connection_id"])
    op.create_index("ix_drafts_wp_object_id", "drafts", ["wp_object_id"])

    # --- publish_history ---------------------------------------------------
    op.create_table(
        "publish_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("wp_object_id", sa.Integer(), nullable=True),
        sa.Column("permalink", sa.String(length=1000), nullable=True),
        sa.Column("operation", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_publish_history"),
    )
    op.create_index("ix_publish_history_object_type", "publish_history", ["object_type"])
    op.create_index("ix_publish_history_wp_object_id", "publish_history", ["wp_object_id"])
    op.create_index("ix_publish_history_status", "publish_history", ["status"])
    op.create_index(
        "ix_publish_history_idempotency_key",
        "publish_history",
        ["idempotency_key"],
    )

    # --- audit_reports -----------------------------------------------------
    op.create_table(
        "audit_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("audit_type", sa.String(length=60), nullable=False),
        sa.Column("site_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("summary_status", sa.String(length=20), nullable=False, server_default="ok"),
        sa.Column("findings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_audit_reports"),
    )
    op.create_index("ix_audit_reports_audit_type", "audit_reports", ["audit_type"])
    op.create_index("ix_audit_reports_site_url", "audit_reports", ["site_url"])

    # --- prompt_templates --------------------------------------------------
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("template_type", sa.String(length=40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_prompt_templates"),
    )
    op.create_index("ix_prompt_templates_template_type", "prompt_templates", ["template_type"])
    op.create_index("ix_prompt_templates_is_default", "prompt_templates", ["is_default"])

    # --- media_records -----------------------------------------------------
    op.create_table(
        "media_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wp_media_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("mime", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_media_records"),
    )
    op.create_index("ix_media_records_wp_media_id", "media_records", ["wp_media_id"])
    op.create_index("ix_media_records_filename", "media_records", ["filename"])
    op.create_index("ix_media_records_content_hash", "media_records", ["content_hash"])

    # --- job_logs ----------------------------------------------------------
    op.create_table(
        "job_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("job_type", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_job_logs"),
        sa.UniqueConstraint("job_id", name="uq_job_logs_job_id"),
    )
    op.create_index("ix_job_logs_status", "job_logs", ["status"])
    op.create_index("ix_job_logs_job_type", "job_logs", ["job_type"])
    op.create_index("ix_job_logs_scheduled_at", "job_logs", ["scheduled_at"])

    # --- app_settings ------------------------------------------------------
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("key", name="pk_app_settings"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")

    op.drop_index("ix_job_logs_scheduled_at", table_name="job_logs")
    op.drop_index("ix_job_logs_job_type", table_name="job_logs")
    op.drop_index("ix_job_logs_status", table_name="job_logs")
    op.drop_table("job_logs")

    op.drop_index("ix_media_records_content_hash", table_name="media_records")
    op.drop_index("ix_media_records_filename", table_name="media_records")
    op.drop_index("ix_media_records_wp_media_id", table_name="media_records")
    op.drop_table("media_records")

    op.drop_index("ix_prompt_templates_is_default", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_template_type", table_name="prompt_templates")
    op.drop_table("prompt_templates")

    op.drop_index("ix_audit_reports_site_url", table_name="audit_reports")
    op.drop_index("ix_audit_reports_audit_type", table_name="audit_reports")
    op.drop_table("audit_reports")

    op.drop_index("ix_publish_history_idempotency_key", table_name="publish_history")
    op.drop_index("ix_publish_history_status", table_name="publish_history")
    op.drop_index("ix_publish_history_wp_object_id", table_name="publish_history")
    op.drop_index("ix_publish_history_object_type", table_name="publish_history")
    op.drop_table("publish_history")

    op.drop_index("ix_drafts_wp_object_id", table_name="drafts")
    op.drop_index("ix_drafts_connection_id", table_name="drafts")
    op.drop_index("ix_drafts_object_type", table_name="drafts")
    op.drop_table("drafts")

    op.drop_table("connections")