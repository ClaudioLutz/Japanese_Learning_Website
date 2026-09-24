"""ReviewLog.undo_snapshot: Vorzustand einer Bewertung fuer „Rueckgaengig".

Speichert beim Bewerten den Zustand VOR dem Review als JSON (CardReviewState-
Felder, vergebene XP, Mastery-/Aggregat-Deltas, CH-Aggregat-Datum). Damit kann
POST /api/srs/undo die juengste Bewertung eines Users exakt zuruecknehmen.

Nullable und rein additiv (ADD COLUMN) — Altdaten behalten NULL und sind damit
schlicht nicht rueckgaengig machbar.

Revision ID: review_log_undo_snapshot
Revises: user_created_at_last_login
Create Date: 2026-09-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'review_log_undo_snapshot'
down_revision = 'user_created_at_last_login'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('undo_snapshot', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.drop_column('undo_snapshot')
