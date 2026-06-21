"""Seedet das Forum mit ein paar ECHTEN Start-Threads (Cold-Start-Hebel).

Inhalte sind von Hand verfasst (N5-konform, deutsche Lerner-/Betreiber-Stimme) —
KEIN externes LLM. Idempotent: ueberspringt Threads, deren Titel in der
Kategorie schon existiert. Autor wird per Username aufgeloest (portabel ueber
Dev/Prod). Ankuendigungen kommen vom Admin, der Rest von Claudios echtem Konto.

Verwendung (lokal/Dev):
    python scripts/seed_forum_threads.py

Auf Prod (hp-ubuntu) im Container:
    sudo docker exec -i japanese_app python - < scripts/seed_forum_threads.py
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from app.models import ForumCategory, ForumPost, ForumTopic, User  # noqa: E402


# Staffelung der Erstell-Daten, damit das Forum nicht wie ein Bot-Dump in einer
# Sekunde aussieht (alles in den letzten ~2 Wochen). days_ago pro Thread.
THREADS = [
    {
        "category": "ankuendigungen",
        "author": "admin",
        "days_ago": 12,
        "title": "Willkommen im Forum \U0001F44B",
        "body": (
            "Schön, dass du hier bist! \U0001F338\n\n"
            "Dieses Forum ist ein kleiner, ruhiger Ort zum Austauschen rund ums "
            "Japanischlernen:\n\n"
            "- **Fragen stellen** in „Hilfe & Fragen“ — keine Frage ist zu klein.\n"
            "- **Ideen & Wünsche** für die Plattform in „Vorschläge“.\n"
            "- **Alles rund um Japan & Sprache** in „Off-Topic“.\n\n"
            "Ich (Claudio) lese hier alles mit und antworte, so gut ich kann. "
            "Schreib gern den ersten Beitrag — auch ein einfaches „Hallo“ "
            "oder woran du gerade lernst, freut mich.\n\n"
            "がんばって！(ganbatte — viel Erfolg!)"
        ),
    },
    {
        "category": "ankuendigungen",
        "author": "admin",
        "days_ago": 3,
        "title": "Neu: Fehler direkt melden — auf jeder Karte und Lektion",
        "body": (
            "Kleine, aber feine Neuerung: Du kannst jetzt **Fehler direkt dort "
            "melden, wo sie auftauchen**.\n\n"
            "- Auf jeder **Lernkarte** (beim Wiederholen, in Lektionen, im Stöbern) "
            "gibt es einen kleinen **⚑ melden**-Link.\n"
            "- Auch oben in jeder **Lektion** findest du „Fehler in dieser Lektion melden“.\n\n"
            "Dein Hinweis landet im Bereich **Hinweise & Korrekturen**. Ich schaue ihn "
            "mir an, korrigiere den Inhalt — und du bekommst eine kurze Rückmeldung, "
            "sobald es erledigt ist.\n\n"
            "Tippfehler, eine holprige Übersetzung, eine seltsame Lesung — alles ist "
            "willkommen. Danke fürs Mithelfen! \U0001F64F"
        ),
    },
    {
        "category": "hilfe-fragen",
        "author": "claudio.lutz.cv",
        "days_ago": 9,
        "title": "は (wa) vs が (ga) — der Merksatz, der bei mir endlich klickte",
        "body": (
            "Lange habe ich は und が durcheinandergebracht. Was mir geholfen hat, "
            "ist diese grobe Faustregel (für den Anfang — es gibt Ausnahmen):\n\n"
            "- **は (wa)** macht das **Thema** auf: „Was das Folgende betrifft …“. "
            "Es zeigt, *worüber* wir reden.\n"
            "- **が (ga)** markiert das **Subjekt** und betont das **Was/Wer** — oft bei "
            "neuer Information oder als Antwort auf „wer?“.\n\n"
            "Zwei Beispiele:\n\n"
            "> わたし**は** がくせい です。\n"
            "> watashi **wa** gakusei desu. — „Ich bin Studentin.“ (Thema: ich)\n\n"
            "> だれ**が** きましたか。 — ともだち**が** きました。\n"
            "> dare **ga** kimashita ka? — tomodachi **ga** kimashita. "
            "— „Wer ist gekommen? — Eine Freundin ist gekommen.“ (das *Wer* steht im Fokus → が)\n\n"
            "Faustregel, die bei mir hängengeblieben ist: **Antwort auf eine "
            "„Wer/Was?“-Frage → meist が. Sonst, beim „darüber rede ich“ → は.**\n\n"
            "Wie merkt ihr euch den Unterschied?"
        ),
    },
    {
        "category": "hilfe-fragen",
        "author": "claudio.lutz.cv",
        "days_ago": 6,
        "title": "Zählwörter: 〜つ, 〜こ, 〜にん, 〜まい — wann nehme ich was?",
        "body": (
            "Zählwörter (Counter) waren für mich am Anfang ein Stolperstein. Die "
            "wichtigsten für N5:\n\n"
            "- **〜つ** — universeller „Joker“ für allgemeine Dinge (bis 9). "
            "ひとつ, ふたつ, みっつ …\n"
            "- **〜こ (個)** — kleine, kompakte Dinge (Äpfel, Bälle, Eier). "
            "りんご さんこ = drei Äpfel.\n"
            "- **〜にん (人)** — Personen. がくせい よにん = vier Studenten. "
            "(Achtung: ひとり = 1 Person, ふたり = 2 Personen sind Sonderformen!)\n"
            "- **〜まい (枚)** — flache, dünne Dinge (Papier, Tickets, T-Shirts). "
            "きっぷ にまい = zwei Tickets.\n\n"
            "Mein Tipp: Wenn dir das passende Zählwort nicht einfällt, kommst du mit "
            "**〜つ** (bis 9) oft durch — das klingt natürlicher als ein falsches "
            "spezielles Zählwort.\n\n"
            "Habt ihr eins, das euch ständig reinrutscht?"
        ),
    },
    {
        "category": "vorschlaege",
        "author": "claudio.lutz.cv",
        "days_ago": 5,
        "title": "Was wünscht ihr euch als Nächstes? (Roadmap-Input)",
        "body": (
            "Ich baue die Plattform Stück für Stück weiter und würde gern wissen, "
            "was **euch** am meisten helfen würde.\n\n"
            "Ein paar Sachen, die ich auf dem Zettel habe:\n\n"
            "- ein **Hör-Modus** (Wort hören → erkennen/tippen)\n"
            "- mehr **Beispielsätze** pro Vokabel\n"
            "- ein **Tipp-Modus** für die Produktion (DE → JP selbst schreiben)\n\n"
            "Was fehlt euch? Was nervt euch? Schreibt's einfach drunter — auch kleine "
            "Wünsche sind willkommen. Ich kann nicht alles sofort umsetzen, aber ich "
            "lese jeden Vorschlag. \U0001F64F"
        ),
    },
    {
        "category": "off-topic",
        "author": "claudio.lutz.cv",
        "days_ago": 4,
        "title": "Womit übt ihr Hören? (Anime, Podcasts, YouTube)",
        "body": (
            "Lesen und Vokabeln klappen bei mir okay, aber **Hören** ist nochmal eine "
            "eigene Baustelle. \U0001F442\n\n"
            "Ich sammle gerade Quellen für Anfänger und bin neugierig, was bei euch "
            "funktioniert:\n\n"
            "- Anime mit (japanischen!) Untertiteln?\n"
            "- langsame Podcasts für Lernende?\n"
            "- YouTube-Kanäle?\n\n"
            "Teilt gern eure Tipps — am besten mit einem kurzen Wort, *warum* es für "
            "N5 passt (z.B. „spricht langsam“, „viel Alltag“)."
        ),
    },
    {
        "category": "off-topic",
        "author": "claudio.lutz.cv",
        "days_ago": 1,
        "title": "Vokabel der Woche: たいへん (taihen)",
        "body": (
            "Kleine neue Reihe — jede Woche ein nützliches Wort. \U0001F5D3️\n\n"
            "**たいへん (taihen)** — 大変 hat zwei Seiten:\n\n"
            "1. **„schlimm / anstrengend / schwierig“** → "
            "しごとが たいへん です。 (shigoto ga taihen desu) "
            "— „Die Arbeit ist anstrengend.“\n"
            "2. als Verstärker **„sehr / wirklich“** → "
            "たいへん ありがとうございます。 "
            "— „Vielen herzlichen Dank.“\n\n"
            "Man hört es ständig im Alltag — sehr praktisch.\n\n"
            "Kennt ihr es schon? Und welches Wort sollen wir nächste Woche nehmen?"
        ),
    },
]


def _get_author(username, cache):
    if username not in cache:
        cache[username] = User.query.filter_by(username=username).first()
    return cache[username]


def seed():
    now = datetime.utcnow()
    created, skipped, problems = 0, 0, 0
    author_cache = {}

    for spec in THREADS:
        cat = ForumCategory.query.filter_by(slug=spec["category"]).first()
        if cat is None:
            print(f"  ! Kategorie fehlt: {spec['category']} — uebersprungen")
            problems += 1
            continue
        author = _get_author(spec["author"], author_cache)
        if author is None:
            print(f"  ! Autor fehlt: {spec['author']} — uebersprungen")
            problems += 1
            continue
        # Idempotent: gleicher Titel in derselben Kategorie -> skip
        existing = ForumTopic.query.filter_by(
            category_id=cat.id, title=spec["title"], is_deleted=False,
        ).first()
        if existing is not None:
            print(f"  = vorhanden: {spec['title']}")
            skipped += 1
            continue

        ts = now - timedelta(days=spec.get("days_ago", 0))
        topic = ForumTopic(
            category_id=cat.id,
            author_id=author.id,
            title=spec["title"],
            created_at=ts,
            last_activity_at=ts,
        )
        db.session.add(topic)
        db.session.flush()  # ID fuer den Slug
        topic.slug = topic.build_slug()

        op = ForumPost(
            topic_id=topic.id,
            author_id=author.id,
            body=spec["body"],
            is_op=True,
            created_at=ts,
        )
        db.session.add(op)
        db.session.commit()
        created += 1
        print(f"  + erstellt: [{spec['category']}] {spec['title']} (von {author.username})")

    print(f"Fertig: {created} erstellt, {skipped} vorhanden, {problems} Probleme.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
