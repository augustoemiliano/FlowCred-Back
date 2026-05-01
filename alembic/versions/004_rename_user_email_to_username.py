"""rename users.email -> users.username

Revision ID: 004_rename_user_email_to_username
Revises: 003_proposals_domain
Create Date: 2026-05-01

"""

import sqlalchemy as sa
from alembic import op

revision = "004_rename_user_email_to_username"
down_revision = "003_proposals_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "username" in cols:
        return
    if "email" not in cols:
        return
    op.alter_column(
        "users",
        "email",
        new_column_name="username",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "email" in cols:
        return
    if "username" not in cols:
        return
    op.alter_column(
        "users",
        "username",
        new_column_name="email",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
