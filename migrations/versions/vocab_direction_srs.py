"""SRS-Lernrichtung: direction-Spalte (forward/reverse) + Vokabel-Produktions-Cue

Fuehrt die Produktions-Richtung (DE->JP) als eigene FSRS-Spur ein:
- card_review_state.direction + review_log.direction ('forward'|'reverse'),
  Default 'forward' (Altdaten bleiben Rezeption).
- Unique-Key card_review_state: (user_id, content_id) -> (user_id, content_id, direction),
  damit forward- und reverse-Karte desselben Items koexistieren.
- vocabulary.production_cue_de: deutscher Disambiguierungs-Hinweis (nullable, additiv).

UPGRADE ist additiv und verlustfrei: bestehende Zeilen werden per server_default
zu 'forward', die neue 3-Spalten-Unique haelt (alle Altzeilen sind 'forward', also
auf (user,content) bereits eindeutig).

DOWNGRADE loescht bewusst alle 'reverse'-Zeilen (sonst scheitert das Wiederherstellen
der 2-Spalten-Unique an Duplikaten) — dokumentierter Daten*verlust* des Downgrades;
Reverse ist ein additives Opt-in-Feature.

Revision ID: vocab_direction_srs
Revises: forum_tables
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'vocab_direction_srs'
down_revision = 'forum_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Additive Spalten (server_default fuellt Altzeilen ohne UPDATE)
    op.add_column('card_review_state',
                  sa.Column('direction', sa.String(length=8), nullable=False,
                            server_default='forward'))
    op.add_column('review_log',
                  sa.Column('direction', sa.String(length=8), nullable=False,
                            server_default='forward'))
    op.add_column('vocabulary',
                  sa.Column('production_cue_de', sa.Text(), nullable=True))

    # 2) Index fuer richtungsgetrennte Optimizer-/Statistik-Queries auf review_log
    op.create_index('ix_reviewlog_user_direction', 'review_log',
                    ['user_id', 'direction'], unique=False)

    # 3) Unique-Key umstellen: (user,content) -> (user,content,direction)
    op.drop_constraint('uq_user_content_review', 'card_review_state', type_='unique')
    op.create_unique_constraint('uq_user_content_direction', 'card_review_state',
                                ['user_id', 'content_id', 'direction'])


def downgrade():
    # Reverse-Zeilen ZUERST loeschen — sonst Duplicate-Key beim Recreate der
    # 2-Spalten-Unique (forward+reverse je (user,content)).
    op.execute("DELETE FROM review_log WHERE direction = 'reverse'")
    op.execute("DELETE FROM card_review_state WHERE direction = 'reverse'")

    op.drop_constraint('uq_user_content_direction', 'card_review_state', type_='unique')
    op.create_unique_constraint('uq_user_content_review', 'card_review_state',
                                ['user_id', 'content_id'])

    op.drop_index('ix_reviewlog_user_direction', table_name='review_log')
    op.drop_column('vocabulary', 'production_cue_de')
    op.drop_column('review_log', 'direction')
    op.drop_column('card_review_state', 'direction')
