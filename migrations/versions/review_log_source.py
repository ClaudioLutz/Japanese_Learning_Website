"""ReviewLog.source: Herkunft einer Bewertung (deck | review | produktion |
kana_grid | dashboard).

Ohne dieses Feld laesst sich nicht unterscheiden, ob eine Karte im Lektions-Deck
(Erstkontakt) oder in einer echten Wiederholung bewertet wurde. Genau diese
Unterscheidung braucht (a) die Deckelung der ersten Deck-Bewertung und (b) die
„Schon entdeckt?"-Ableitung im Willkommen-zurueck-Dialog.

Nullable und rein additiv (ADD COLUMN) — Altdaten behalten NULL, unbekannte
Werte werden serverseitig zu NULL normalisiert.

Revision ID: review_log_source
Revises: lesson_last_page
Create Date: 2026-09-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'review_log_source'
down_revision = 'lesson_last_page'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=16), nullable=True))


def downgrade():
    with op.batch_alter_table('review_log', schema=None) as batch_op:
        batch_op.drop_column('source')
