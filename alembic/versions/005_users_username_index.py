"""alinha users.username com o modelo (tamanho 64 e índice ix_users_username)

A migração 004 renomeou a coluna email -> username, mas manteve o índice
ix_users_email e o tamanho VARCHAR(255). Esta revisão deixa o esquema igual
ao modelo SQLAlchemy (o `alembic check` passa a não detetar diferenças).

Revision ID: 005_users_username_index
Revises: 004_rename_user_email_to_username
Create Date: 2026-11-02

"""

import sqlalchemy as sa

from alembic import op

revision = "005_users_username_index"
down_revision = "004_rename_user_email_to_username"
branch_labels = None
depends_on = None


def _index_names() -> set[str]:
    insp = sa.inspect(op.get_bind())
    return {ix["name"] for ix in insp.get_indexes("users")}


def upgrade() -> None:
    indexes = _index_names()
    with op.batch_alter_table("users") as batch:
        if "ix_users_email" in indexes:
            batch.drop_index("ix_users_email")
        batch.alter_column(
            "username",
            existing_type=sa.String(length=255),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        if "ix_users_username" not in indexes:
            batch.create_index("ix_users_username", ["username"], unique=True)


def downgrade() -> None:
    indexes = _index_names()
    with op.batch_alter_table("users") as batch:
        if "ix_users_username" in indexes:
            batch.drop_index("ix_users_username")
        batch.alter_column(
            "username",
            existing_type=sa.String(length=64),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
        batch.create_index("ix_users_email", ["username"], unique=True)
