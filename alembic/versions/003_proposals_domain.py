"""proposals checklist history documents

Revision ID: 003_proposals_domain
Revises: 002_clients_table
Create Date: 2026-04-30

"""

import sqlalchemy as sa
from alembic import op

revision = "003_proposals_domain"
down_revision = "002_clients_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proposals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("bank", sa.String(length=255), nullable=False),
        sa.Column("property_value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("financed_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("responsible_user_id", sa.Integer(), nullable=False),
        sa.Column("next_stage_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proposals_bank"), "proposals", ["bank"], unique=False)
    op.create_index(op.f("ix_proposals_client_id"), "proposals", ["client_id"], unique=False)
    op.create_index(op.f("ix_proposals_responsible_user_id"), "proposals", ["responsible_user_id"], unique=False)
    op.create_index(op.f("ix_proposals_status"), "proposals", ["status"], unique=False)

    op.create_table(
        "proposal_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proposal_history_proposal_id"), "proposal_history", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_proposal_history_user_id"), "proposal_history", ["user_id"], unique=False)

    op.create_table(
        "proposal_checklist_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_proposal_checklist_items_proposal_id"),
        "proposal_checklist_items",
        ["proposal_id"],
        unique=False,
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("storage_name", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=127), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_name"),
    )
    op.create_index(op.f("ix_documents_proposal_id"), "documents", ["proposal_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_proposal_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_proposal_checklist_items_proposal_id"), table_name="proposal_checklist_items")
    op.drop_table("proposal_checklist_items")
    op.drop_index(op.f("ix_proposal_history_user_id"), table_name="proposal_history")
    op.drop_index(op.f("ix_proposal_history_proposal_id"), table_name="proposal_history")
    op.drop_table("proposal_history")
    op.drop_index(op.f("ix_proposals_status"), table_name="proposals")
    op.drop_index(op.f("ix_proposals_responsible_user_id"), table_name="proposals")
    op.drop_index(op.f("ix_proposals_client_id"), table_name="proposals")
    op.drop_index(op.f("ix_proposals_bank"), table_name="proposals")
    op.drop_table("proposals")
