"""Schreibt die 4 Prosa-text-Pages von Lesson 144 in Markdown um.

User-Direktive 2026-04-25: Texte sollen visuell formatiert sein (Headlines,
Bold, Listen) — vorher sah alles gleich aus. Page 5 (Dialog) bleibt unveraendert.

Betroffene LessonContent-IDs:
- 6159 (Page 1, Einfuehrung)
- 6183 (Page 4, Grammatik-Intro)
- 6188 (Page 6, Quiz-Intro)
- 6189 (Page 7, Zusammenfassung)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app import create_app, db
from app.models import LessonContent

PAGE_1_INTRO = """\
## Zwei Wortgruppen statt einer

Im Deutschen sagst du immer **"mein Vater"** und **"der Vater meiner Freundin"** mit demselben Wort. Im Japanischen ist das anders: Es gibt **zwei komplette Wortgruppen** für Familienmitglieder — eine für die *eigene* Familie (bescheiden) und eine für die Familie *anderer Leute* (höflich).

### Beispiel: Vater

- Eigener Vater → 「ちち」 *(chichi)* — bescheiden
- Vater einer anderen Person (oder direkte Anrede) → 「おとうさん」 *(otousan)* — höflich

Dasselbe Prinzip gilt für **Mutter, ältere Geschwister, Onkel, Tante** — wirklich jedes Familienmitglied.

### Die Logik dahinter: 「うち」 vs. 「そと」

Das wirkt am Anfang ungewohnt, hat aber eine klare Logik: Es ist Teil der japanischen 「うち」 *(uchi, 'innen')* und 「そと」 *(soto, 'aussen')* Unterscheidung.

> Über die eigene Gruppe sprichst du **bescheiden**, über andere **höflich**. Wer das durcheinanderbringt, klingt entweder arrogant oder kindlich.

### Was du in dieser Lektion lernst

1. **23 Familienvokabeln** — beide Reihen plus Sammelbegriffe
2. **3 Grammatikmuster** — uchi/soto, das Possessiv 「の」 *(no)*, das Existenzverb 「います」 *(imasu)* für Personen
3. **Mini-Dialog** — Tanaka stellt seine Familie vor

Am Ende kannst du sagen, wieviele Personen zu deiner Familie gehören, jedes Mitglied benennen und nach der Familie deines Gegenübers fragen — mit der **richtigen Höflichkeitsstufe**.
"""

PAGE_4_GRAMMAR = """\
## Drei Muster für jedes Familiengespräch

Drei Grammatikbausteine reichen, um über jede Familie souverän zu sprechen.

### 1. 「うち」 vs. 「そと」 — wer gehört dazu?

Über die **eigene Familie** sprichst du bescheiden:

- 「ちち」 *(chichi)* — mein Vater
- 「はは」 *(haha)* — meine Mutter
- 「あに」 *(ani)* — mein älterer Bruder

Über die Familie **anderer Leute** sprichst du höflich:

- 「おとうさん」 *(otousan)* — Vater
- 「おかあさん」 *(okaasan)* — Mutter
- 「おにいさん」 *(oniisan)* — älterer Bruder

> Wenn du dein Gegenüber direkt nach seinem Vater fragst, nutzt du **immer** die höfliche Form: 「おとうさんは おげんきですか」 *(otousan wa ogenki desu ka, 'Geht es Ihrem Vater gut?')*.

### 2. Possessiv 「の」 — das japanische Genitiv

Das Partikel 「の」 *(no)* verbindet **Besitzer + Besessenes**, ähnlich dem deutschen Genitiv:

- 「わたしの かぞく」 *(watashi no kazoku)* — **meine** Familie
- 「たなかさんの おとうさん」 *(Tanaka-san no otousan)* — Tanaka-sans **Vater**

Reihenfolge: `[Besitzer] + の + [Besessenes]`. Du kannst mehrere 「の」 *(no)* verketten:

> 「ともだちの おかあさんの 名前」 *(tomodachi no okaasan no namae)* — der Name der Mutter meines Freundes.

### 3. 「います」 für Personen — wer existiert?

Im Japanischen gibt es **zwei Existenzverben**:

- 「あります」 *(arimasu)* → für **leblose Dinge** (Bücher, Stühle, Geld)
- 「います」 *(imasu)* → für **Lebewesen** (Menschen, Tiere)

Familienmitglieder sind Lebewesen, also immer 「います」 *(imasu)*:

- 「あにが 二人 います」 *(ani ga futari imasu)* — Ich habe zwei ältere Brüder.
- 「こどもが いません」 *(kodomo ga imasen)* — Ich habe keine Kinder.

Achte auf die Partikel: **「が」** *(ga)* markiert die Person, deren Existenz du angibst.
"""

PAGE_6_QUIZ_INTRO = """\
## Teste dein Familien-Wissen

**Vierzehn Fragen** zu Familienvokabeln, uchi/soto-Unterscheidung und der 「ます」 *(masu)* -Form von 「います」 *(imasu)*.

- **Multiple Choice** — die richtige Übersetzung wählen
- **Richtig / Falsch** — Aussagen bewerten
- **Zuordnen** — Japanisch ↔ Deutsch verbinden
"""

PAGE_7_SUMMARY = """\
## Was du jetzt kannst

### 23 Familienvokabeln im Überblick

**Eigene Familie (bescheiden):**

- 「ちち」 *(chichi)* — Vater
- 「はは」 *(haha)* — Mutter
- 「あに / あね」 *(ani / ane)* — älterer Bruder / ältere Schwester
- 「おとうと / いもうと」 *(otouto / imouto)* — jüngerer Bruder / jüngere Schwester

**Andere Familie (höflich):**

- 「おとうさん / おかあさん」 *(otousan / okaasan)*
- 「おにいさん / おねえさん」 *(oniisan / oneesan)*

**Sammelbegriffe & Personen:**

- 「かぞく」 *(kazoku)* — Familie
- 「きょうだい」 *(kyoudai)* — Geschwister
- 「りょうしん」 *(ryoushin)* — Eltern
- 「こども」 *(kodomo)* — Kind
- 「人」 *(hito)*, 「男」 *(otoko)*, 「女」 *(onna)*, 「男の子」 *(otoko no ko)*, 「女の子」 *(onna no ko)*, 「ともだち」 *(tomodachi)*

### Drei Grammatikmuster

1. **uchi/soto** — eigene vs. fremde Familie
2. **Possessiv 「の」** *(no)* — `[Besitzer] + の + [Besessenes]`
3. **Existenzverb 「います」** *(imasu)* — für Personen, nicht 「あります」 *(arimasu)*

> **Faustregel:** Über uns selbst klein, über andere gross. Lebewesen bekommen 「います」 *(imasu)*, Dinge bekommen 「あります」 *(arimasu)*.

### Standard-Smalltalk

Im Dialog hast du gesehen, wie sich Tanaka und Lisa über ihre Familien austauschen — eine sehr typische erste Konversation in Japan:

- 「かぞくは 何人ですか」 *(kazoku wa nan-nin desu ka)* — Wie viele Personen sind in deiner Familie?
- 「きょうだいは いますか」 *(kyoudai wa imasu ka)* — Hast du Geschwister?

### Ausblick

In der nächsten Lektion baust du darauf auf: Du lernst **Berufe** und kannst dann sagen, was deine Familienmitglieder beruflich machen — 「父は エンジニアです」 *(chichi wa enjinia desu, 'Mein Vater ist Ingenieur')*.
"""

UPDATES = {
    6159: PAGE_1_INTRO,
    6183: PAGE_4_GRAMMAR,
    6188: PAGE_6_QUIZ_INTRO,
    6189: PAGE_7_SUMMARY,
}

app = create_app()
with app.app_context():
    for lc_id, new_text in UPDATES.items():
        lc = LessonContent.query.get(lc_id)
        if not lc:
            print(f"[FEHLER] LessonContent {lc_id} nicht gefunden.")
            continue
        lc.content_text = new_text
        print(f"[OK] LessonContent {lc_id} ({lc.title!r}): {len(new_text)} Zeichen Markdown.")
    db.session.commit()
    print("[OK] Commit fertig.")
