"""LessonCategory.image_url: Modul-Banner (16:9) fuer die Lernpfad-Karten
auf der Startseite und im /learn/n5-Hub.

Nullable — Module ohne Bild fallen im Template auf das Emoji-Icon zurueck.
Wert ist ein uploads-relativer Pfad, z.B. 'modules/module_n5-hiragana.webp'
(serviert via routes.uploaded_file), analog Lesson.thumbnail_url.

Revision ID: lesson_category_image_url
Revises: review_log_stage_at_review
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'lesson_category_image_url'
down_revision = 'review_log_stage_at_review'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lesson_category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('lesson_category', schema=None) as batch_op:
        batch_op.drop_column('image_url')
