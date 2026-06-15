"""ReviewLog.stage_at_review: SRS-Stufe (0..9) vor dem Review fuer die
„Genauigkeit nach Reife"-Statistik des Lernenden-Dashboards (/api/dashboard/acc-by-stage).

Nullable — Altdaten vor Einfuehrung haben keinen Wert; die Spalte fuellt sich
ab jetzt pro Review (Decision 2026-06-15: exakt mitloggen statt approximieren).

Revision ID: review_log_stage_at_review
Revises: kana_storm_score_table
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'review_log_stage_at_review'
down_revision = 'kana_storm_score_table'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stage_at_review', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.drop_column('stage_at_review')
