"""add quote_journey_events

Revision ID: c8e4a91d2b7f
Revises: f4318b2b2f9a
Create Date: 2026-08-25 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8e4a91d2b7f"
down_revision: Union[str, None] = "f4318b2b2f9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "quote_journey_events" in inspector.get_table_names():
        return

    op.create_table(
        "quote_journey_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("location_id", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("quote_premium", sa.Float(), nullable=True),
        sa.Column("quote_coverage_period", sa.Integer(), nullable=True),
        sa.Column("quote_frequency", sa.Float(), nullable=True),
        sa.Column("quote_severity", sa.Float(), nullable=True),
        sa.Column("quote_event_id", sa.String(), nullable=True),
        sa.Column("quote_status", sa.String(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_quote_journey_events_user_id_users")),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], name=op.f("fk_quote_journey_events_location_id_locations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_journey_events")),
    )
    with op.batch_alter_table("quote_journey_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_quote_journey_events_session_id"), ["session_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_quote_journey_events_event_type"), ["event_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_quote_journey_events_created_at"), ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "quote_journey_events" not in inspector.get_table_names():
        return

    with op.batch_alter_table("quote_journey_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_quote_journey_events_created_at"))
        batch_op.drop_index(batch_op.f("ix_quote_journey_events_event_type"))
        batch_op.drop_index(batch_op.f("ix_quote_journey_events_session_id"))
    op.drop_table("quote_journey_events")
