"""User.created_at und User.last_login — Nutzeranalyse ueberhaupt erst moeglich.

Die `user`-Tabelle hatte bisher keinen einzigen Konto-Zeitstempel. Damit liess
sich weder sagen, wann jemand dazugekommen ist, noch ob ein Konto ueberhaupt je
benutzt wurde (relevant seit der XSS-Probe-Registrierung und dem
Bot-Verdachtskonto in Produktion).

Beide Spalten sind nullable und rein additiv (ADD COLUMN).

Backfill im Upgrade (nur PostgreSQL): `created_at` bestehender Nutzer wird auf
den fruehesten Zeitstempel gesetzt, den der Nutzer in irgendeiner
Aktivitaetstabelle hinterlassen hat. Das ist eine Untergrenze fuer das echte
Registrierungsdatum, aber die einzige rekonstruierbare Naeherung. Nutzer ohne
jede Spur bleiben NULL — bewusst, statt ein Datum zu erfinden.
`last_login` wird NICHT rueckwirkend geraten (es gibt keine Datenquelle dafuer).

Revision ID: user_created_at_last_login
Revises: review_log_source
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'user_created_at_last_login'
down_revision = 'review_log_source'
branch_labels = None
depends_on = None


# (Tabelle, Zeitstempel-Spalte) — alle haben user_id und einen Entstehungs-
# Zeitpunkt. Bewusst ausgelassen: kana_confusion.last_seen (ist "zuletzt", nicht
# "zuerst") und daily_review_aggregate.review_date (nur DATE-Granularitaet).
ACTIVITY_SOURCES = [
    ('user_lesson_progress', 'started_at'),
    ('review_log', 'reviewed_at'),
    ('user_quiz_answer', 'answered_at'),
    ('card_review_state', 'created_at'),
    ('kana_spell_score', 'created_at'),
    ('kana_storm_score', 'created_at'),
    ('user_achievement', 'unlocked_at'),
    ('lesson_purchase', 'purchased_at'),
    ('course_purchase', 'purchased_at'),
    ('payment_transaction', 'created_at'),
]


def _backfill_sql():
    union = '\n            UNION ALL '.join(
        f'SELECT user_id, {col} AS ts FROM {table}'
        for table, col in ACTIVITY_SOURCES
    )
    return f"""
        UPDATE "user" AS u
        SET created_at = a.first_seen
        FROM (
            SELECT user_id, MIN(ts) AS first_seen
            FROM (
            {union}
            ) AS spuren
            WHERE user_id IS NOT NULL AND ts IS NOT NULL
            GROUP BY user_id
        ) AS a
        WHERE u.id = a.user_id AND u.created_at IS NULL
    """


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))

    bind = op.get_bind()
    # UPDATE ... FROM ist Postgres-Syntax. Tests laufen ueber create_all, der
    # Backfill ist dort weder noetig noch lauffaehig.
    if bind.dialect.name == 'postgresql':
        op.execute(sa.text(_backfill_sql()))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('created_at')
