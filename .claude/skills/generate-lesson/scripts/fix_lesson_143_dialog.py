"""Fix Lesson 143 dialog format to match MNN DE style (-> instead of →)
and correct Lisa's phone number typo (ぜろななぎん → ぜろななきゅう)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import LessonContent

NEW_DIALOG = """Tanaka Haruto arbeitet in Zürich und lernt auf einer Willkommensparty seine neue Kollegin Lisa Weber kennen. Sie tauschen Alter und Telefonnummern aus, damit sie sich verabreden können.

Tanaka: はじめまして。たなか はるとです。
  (Hajimemashite. Tanaka Haruto desu.)
  -> Freut mich. Ich bin Tanaka Haruto.

Lisa: はじめまして。リサ・ウェーバーです。よろしく おねがいします。
  (Hajimemashite. Risa Weebaa desu. Yoroshiku onegaishimasu.)
  -> Freut mich. Ich bin Lisa Weber. Angenehm.

Tanaka: リサさんは なんさいですか。
  (Risa-san wa nansai desu ka.)
  -> Wie alt sind Sie, Lisa?

Lisa: にじゅうはっさいです。たなかさんは。
  (Nijuuhassai desu. Tanaka-san wa.)
  -> Ich bin 28 Jahre alt. Und Sie, Tanaka-san?

Tanaka: わたしは さんじゅうにさいです。
  (Watashi wa sanjuuni-sai desu.)
  -> Ich bin 32 Jahre alt.

Lisa: そうですか。
  (Sou desu ka.)
  -> Ach so.

Tanaka: リサさんの でんわばんごうは なんばんですか。
  (Risa-san no denwa bangou wa nanban desu ka.)
  -> Wie lautet Ihre Telefonnummer, Lisa?

Lisa: ぜろななきゅうの いちにさんよんの ごろくななはちです。
  (Zero-nana-kyuu no ichi-ni-san-yon no go-roku-nana-hachi desu.)
  -> Sie ist 079-1234-5678.

Tanaka: ありがとうございます。
  (Arigatou gozaimasu.)
  -> Vielen Dank."""

app = create_app()
with app.app_context():
    lc = db.session.query(LessonContent).filter_by(id=6154).first()
    if not lc:
        print("[FEHLER] LessonContent 6154 nicht gefunden")
        sys.exit(1)
    lc.content_text = NEW_DIALOG
    lc.title = "Tanaka trifft Lisa — Willkommensparty"
    db.session.commit()
    print(f"[OK] Dialog fuer Lesson 143 / LC 6154 aktualisiert ({len(NEW_DIALOG)} Zeichen).")
