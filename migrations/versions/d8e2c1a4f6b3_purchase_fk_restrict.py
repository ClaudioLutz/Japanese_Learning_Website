"""Purchase-FKs: CASCADE -> RESTRICT (Schutz vor versehentlichem Datenverlust beim Sync)

Revision ID: d8e2c1a4f6b3
Revises: b7a1c8d9e2f3
Create Date: 2026-04-25

Hintergrund (Audit 2026-04-25):
Die FKs `lesson_purchase.lesson_id` und `course_purchase.course_id` hatten bisher
`ON DELETE CASCADE`. Im Sync-Skript (`scripts/sync_content_upsert.py`) wird der
Cloud-Stand mit dem lokalen Stand abgeglichen — Cloud-Lessons/Cours, die lokal
fehlen (z.B. weil ein Admin sie zwischen Pull und Push erstellt hat), werden auf
Cloud geloescht. Bei CASCADE wuerden Kaeufe stillschweigend mit-geloescht.

Mit RESTRICT wuerde ein solcher DELETE durch die DB blockiert und die ganze
Sync-Transaktion zurueckgerollt — kein stiller Datenverlust.
"""
from alembic import op


revision = 'd8e2c1a4f6b3'
down_revision = 'b7a1c8d9e2f3'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('lesson_purchase_lesson_id_fkey',
                       'lesson_purchase', type_='foreignkey')
    op.create_foreign_key(
        'lesson_purchase_lesson_id_fkey',
        'lesson_purchase', 'lesson',
        ['lesson_id'], ['id'],
        ondelete='RESTRICT',
    )

    op.drop_constraint('course_purchase_course_id_fkey',
                       'course_purchase', type_='foreignkey')
    op.create_foreign_key(
        'course_purchase_course_id_fkey',
        'course_purchase', 'course',
        ['course_id'], ['id'],
        ondelete='RESTRICT',
    )


def downgrade():
    op.drop_constraint('lesson_purchase_lesson_id_fkey',
                       'lesson_purchase', type_='foreignkey')
    op.create_foreign_key(
        'lesson_purchase_lesson_id_fkey',
        'lesson_purchase', 'lesson',
        ['lesson_id'], ['id'],
        ondelete='CASCADE',
    )

    op.drop_constraint('course_purchase_course_id_fkey',
                       'course_purchase', type_='foreignkey')
    op.create_foreign_key(
        'course_purchase_course_id_fkey',
        'course_purchase', 'course',
        ['course_id'], ['id'],
        ondelete='CASCADE',
    )
