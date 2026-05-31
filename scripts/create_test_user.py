"""Legt einen Test-User an und seedet gemischte, fällige SRS-Karten, damit
``/review`` für UI-Tests (z.B. via Playwright) sofort Karten zeigt — Kana,
Vokabeln und Grammatik (inkl. der Cloze-Lückentext-Karten).

Das Passwort wird als CLI-Argument übergeben und NIE im Code/Repo hinterlegt
(es gehört in die gitignorete ``.env``). Idempotent:
- Existiert der User bereits, werden Passwort + Admin-Flag aktualisiert.
- Bereits geseedete Karten werden nicht doppelt angelegt.

CLI:
  python scripts/create_test_user.py --password 'XXX'
        [--email testuser@japanese-learning.ch] [--username testuser]
        [--cards-per-type 8] [--no-admin]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

from fsrs import Card

from app import create_app, db
from app.models import CardReviewState, LessonContent, User

CARD_TYPES = ["kana", "vocabulary", "grammar"]


def _seed_due_cards(user_id: int, per_type: int) -> dict[str, int]:
    """Legt pro Karten-Typ bis zu ``per_type`` fällige CardReviewState an,
    die der User noch nicht hat. Gibt die Anzahl je Typ zurück."""
    existing = {
        cid for (cid,) in db.session.query(CardReviewState.content_id)
        .filter(CardReviewState.user_id == user_id).all()
    }
    # leicht in der Vergangenheit → garantiert fällig (get_due_cards: due <= now)
    due = datetime.utcnow() - timedelta(hours=1)
    added: dict[str, int] = {}
    for ctype in CARD_TYPES:
        items = (
            LessonContent.query
            .filter(LessonContent.content_type == ctype)
            .order_by(LessonContent.id)
            .all()
        )
        count = 0
        for item in items:
            if count >= per_type:
                break
            if item.id in existing:
                continue
            ref = item.get_content_data()
            # Nur Items mit auflösbarem Referenz-Datensatz (sonst leere Karte)
            if ref is None:
                continue
            # Grammar-Platzhalter/„Leichen" überspringen (z.B. structure/
            # example_sentences == "＿＿") — sonst zeigt /review Müll-Romaji.
            if ctype == "grammar":
                es = (getattr(ref, "example_sentences", "") or "").strip()
                if len(es) < 6 or es == "＿＿":
                    continue
            db.session.add(CardReviewState(
                user_id=user_id,
                content_id=item.id,
                fsrs_card_state=Card().to_json(),
                due_date=due,
                status="new",
                reps=0,
                lapses=0,
            ))
            existing.add(item.id)
            count += 1
        added[ctype] = count
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--password", required=True,
                        help="Passwort des Test-Users (aus .env, nicht hardcoden)")
    parser.add_argument("--email", default="testuser@japanese-learning.ch")
    parser.add_argument("--username", default="testuser")
    parser.add_argument("--cards-per-type", type=int, default=8)
    parser.add_argument("--no-admin", action="store_true",
                        help="User OHNE Admin-Rechte anlegen (Default: Admin)")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    app = create_app()
    with app.app_context():
        user = User.query.filter(
            (User.email == args.email) | (User.username == args.username)
        ).first()

        if user:
            action = "aktualisiert"
            user.email = args.email
            user.username = args.username
        else:
            action = "angelegt"
            user = User(username=args.username, email=args.email,
                        subscription_level="premium")
            db.session.add(user)

        user.set_password(args.password)
        user.is_admin = not args.no_admin
        # Sicherstellen, dass der Account einsatzbereit ist (kein Lockout-Rest).
        user.failed_login_count = 0
        user.locked_until = None
        db.session.flush()  # user.id

        seeded = _seed_due_cards(user.id, args.cards_per_type)
        db.session.commit()

        print(f"[OK] Test-User {action}: id={user.id} "
              f"username={user.username!r} email={user.email!r} "
              f"admin={user.is_admin} subscription={user.subscription_level}")
        print("[OK] Fällige Karten geseedet: "
              + ", ".join(f"{k}={v}" for k, v in seeded.items())
              + f" (gesamt {sum(seeded.values())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
