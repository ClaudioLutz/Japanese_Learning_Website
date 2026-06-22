"""UserLessonProgress.last_page: Resume an der zuletzt gelesenen Seite

Speichert die zuletzt besuchte Carousel-Seite (1-basiert) pro Nutzer/Lektion,
damit der "Weiter lernen"-Knopf an die Stelle zurueckspringt, wo der Nutzer
zuletzt war (geraeteuebergreifend, da serverseitig).

STRIKT ADDITIV: legt nur eine neue, nullable Spalte an, ruehrt keine bestehenden
Daten an. Sicher beim automatischen `flask db upgrade` im Prod-Container-Entrypoint.

Revision ID: lesson_last_page
Revises: kana_spell_score
Create Date: 2026-06-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'lesson_last_page'
down_revision = 'kana_spell_score'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user_lesson_progress',
        sa.Column('last_page', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column('user_lesson_progress', 'last_page')
