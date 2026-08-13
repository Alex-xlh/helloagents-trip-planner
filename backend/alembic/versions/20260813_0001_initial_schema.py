"""initial schema

Revision ID: 20260813_0001
Revises:
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260813_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")} if "users" in tables else set()
    if "ix_users_id" not in user_indexes:
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    if "ix_users_username" not in user_indexes:
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "trip_history" not in tables:
        op.create_table(
            "trip_history",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("destination", sa.String(length=100), nullable=False),
            sa.Column("trip_data", sa.JSON(), nullable=False),
            sa.Column("trip_hash", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    history_indexes = {idx["name"] for idx in inspector.get_indexes("trip_history")} if "trip_history" in tables else set()
    if "ix_trip_history_id" not in history_indexes:
        op.create_index(op.f("ix_trip_history_id"), "trip_history", ["id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "trip_history" in tables:
        history_indexes = {idx["name"] for idx in inspector.get_indexes("trip_history")}
        if "ix_trip_history_id" in history_indexes:
            op.drop_index(op.f("ix_trip_history_id"), table_name="trip_history")
        op.drop_table("trip_history")

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" in tables:
        user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_username" in user_indexes:
            op.drop_index(op.f("ix_users_username"), table_name="users")
        if "ix_users_id" in user_indexes:
            op.drop_index(op.f("ix_users_id"), table_name="users")
        op.drop_table("users")
