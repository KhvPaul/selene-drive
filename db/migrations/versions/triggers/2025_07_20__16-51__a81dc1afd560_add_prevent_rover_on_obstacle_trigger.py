"""add prevent_rover_on_obstacle trigger

Revision ID: a81dc1afd560
Revises: 36d3f435847b
Create Date: 2025-07-20 16:51:13.454328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a81dc1afd560"
down_revision = "36d3f435847b"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_rover_on_obstacle()
    RETURNS trigger AS $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM obstacles
            WHERE longitude = NEW.longitude AND latitude = NEW.latitude
        ) THEN
            RAISE EXCEPTION 'Rover cannot land or move to an obstacle at (%s, %s)', NEW.longitude, NEW.latitude;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER trg_prevent_rover_on_obstacle
    BEFORE INSERT ON rover_states
    FOR EACH ROW
    EXECUTE FUNCTION prevent_rover_on_obstacle();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_rover_on_obstacle ON rover_states;")
    op.execute("DROP FUNCTION IF EXISTS prevent_rover_on_obstacle;")
