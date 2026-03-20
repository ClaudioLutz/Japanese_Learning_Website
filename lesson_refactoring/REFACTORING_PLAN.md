# Lektions-Refactoring Plan

**Erstellt:** 20. März 2026
**Aktualisiert:** 20. März 2026
**Status:** Planung

> **Richtungswechsel:** Statt viele mittelmässige Lektionen → wenige Premium-Lektionen
> mit rotem Faden, Storytelling und Audio. Siehe `KONZEPT_PREMIUM_LEKTIONEN.md`.

---

## 1. Ausgangslage

### Aktueller Stand
- 80 Lektionen, 4'184 Content-Items, 3 Kurse in der Datenbank
- 36 Erstellungs-Skripte in `lesson_creation_scripts/`
- Generiert mit **Gemini 2.5 Pro** (Text) + **OpenAI gpt-image-1 / DALL-E 3** (Bilder)
- Thematisch organisiert (Reisen, Kultur, Grammatik etc.), aber **kein strukturierter Lehrplan**
- Alle Lektionen auf Deutsch für deutschsprachige Lernende

### Probleme
1. **Veraltetes KI-Modell**: Gemini 2.5 Pro ist überholt, Gemini 3 Flash ist besser und günstiger
2. **Kein Curriculum**: Lektionen sind thematische Inseln ohne Lernpfad
3. **Kein JLPT-Bezug**: Keine Zuordnung zu Sprachniveaus (N5-N1)
4. **Keine progressive Struktur**: Kein Aufbau von einfach nach komplex
5. **Bildgenerierung teuer**: gpt-image-1 (High) kostet $0.167/Bild

---

## 2. KI-Modell-Migration

### Text-Generierung: Gemini 2.5 Pro → Gemini 3 Flash

| | Gemini 2.5 Pro (alt) | Gemini 3 Flash (neu) |
|---|---|---|
| Input/1M Tokens | $1.25 | $0.50 |
| Output/1M Tokens | $10.00 | $3.00 |
| Japanisch-Qualität | Sehr gut | Besser (übertrifft 2.5 Pro) |
| Geschwindigkeit | Standard | 3x schneller |
| **Kostenersparnis** | — | **~70%** |

**Änderung in `ai_services.py`:**
```python
# Alt:
self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
# Neu:
self.gemini_model = genai.GenerativeModel('gemini-3-flash')
```

### Bild-Generierung: Empfohlene Alternativen

| Modell | Preis/Bild | Anime-Qualität | API | Empfehlung |
|---|---|---|---|---|
| **gpt-image-1 (High)** (aktuell) | $0.167 | Gut | OpenAI | Teuer |
| **gpt-image-1-mini** | $0.036 | Akzeptabel | OpenAI | Budget-OpenAI |
| **Flux 1.1 Pro** | $0.04 | Sehr gut | Black Forest Labs | **Preis-Leistung** |
| **Hunyuan Image 3.0** | $0.03 | Exzellent (Anime) | Tencent / Open Source | **Beste Anime-Qualität** |
| **NovelAI V4.5** | $25/Mt. unlimitiert | Herausragend (Anime) | NovelAI | **Beste Option bei Batch** |
| Google Imagen 4 | $0.02-0.06 | Solide | Vertex AI | Günstig |

**Empfehlung:** Für 500-1'000 Bilder im Anime/Manga-Stil:
- **1. Wahl: Flux 1.1 Pro** — $0.04/Bild, sehr gute Qualität, einfache API
- **2. Wahl: gpt-image-1-mini** — $0.036/Bild, bleibt im OpenAI-Ökosystem (kein Code-Umbau)

**Kostenvergleich für ~1'000 Bilder:**
- Aktuell (gpt-image-1 High): **$167**
- Flux 1.1 Pro: **$40**
- gpt-image-1-mini: **$36**

### Entscheidung offen
- [ ] Gemini 3 Flash: **Bestätigt**
- [ ] Bild-API: Flux 1.1 Pro vs. gpt-image-1-mini vs. andere? → **Test-Vergleich nötig**

---

## 3. Curriculum-Neugestaltung

### Lehrplan-Prinzipien (basierend auf Recherche)

1. **JLPT-orientiert**: Lektionen nach N5 → N4 → N3 → N2 → N1 organisieren
2. **Progressive Struktur**: Jede Lektion baut auf vorherigen auf
3. **Schriftsystem zuerst**: Hiragana → Katakana → Basis-Kanji
4. **Kontextbasiert**: Vokabeln in Sätzen, nicht isoliert
5. **Multi-Skill**: Lesen + Hören + Schreiben + Quiz pro Lektion
6. **SRS-Integration**: Spaced Repetition für Kanji und Vokabeln
7. **Deutschsprachige Didaktik**: Kanji-Komposita ↔ deutsche Komposita nutzen

### Vorgeschlagene Kursstruktur

#### Kurs 1: Grundlagen (Pre-N5)
| # | Lektion | Inhalt |
|---|---------|--------|
| 1 | Willkommen im Japanischen | Überblick: Warum Japanisch? Schriftsysteme erklärt |
| 2 | Hiragana あ-こ (Reihe 1-2) | 10 Zeichen + Aussprache + erste Wörter |
| 3 | Hiragana さ-と (Reihe 3-4) | 10 Zeichen + einfache Wörter |
| 4 | Hiragana な-ほ (Reihe 5-6) | 10 Zeichen + erste Sätze |
| 5 | Hiragana ま-ん (Reihe 7-10) | Restliche Zeichen + Dakuten/Handakuten |
| 6 | Hiragana-Meister | Zusammenfassung + umfassendes Quiz |
| 7 | Katakana ア-コ (Reihe 1-2) | 10 Zeichen + Fremdwörter |
| 8 | Katakana サ-ト (Reihe 3-4) | 10 Zeichen + Fremdwörter |
| 9 | Katakana ナ-ホ (Reihe 5-6) | 10 Zeichen |
| 10 | Katakana マ-ン (Reihe 7-10) | Restliche Zeichen |
| 11 | Katakana-Meister | Zusammenfassung + Quiz |
| 12 | Erste Schritte: Sich vorstellen | はじめまして, Partikel は/です |

#### Kurs 2: N5 — Basis-Japanisch
| # | Lektion | Inhalt |
|---|---------|--------|
| 13 | Zahlen und Zählen | 1-100, Zählwörter (つ, 個) |
| 14 | Zeitangaben | Uhrzeit, Wochentage, Monate |
| 15 | Im Restaurant bestellen | 食べ物-Vokabeln, ください, を-Partikel |
| 16 | Einkaufen gehen | いくらですか, Geldbeträge, これ/それ/あれ |
| 17 | Verben Grundlagen (Gruppe I) | ます-Form, Gegenwart/Zukunft |
| 18 | Verben Grundlagen (Gruppe II) | る-Verben, Verneinung |
| 19 | Adjektive (い und な) | Beschreibungen, Satzbildung |
| 20 | Wegbeschreibung | Ortsangaben, に/で/へ-Partikel |
| 21 | Mein Alltag beschreiben | Tagesablauf, Zeitadverbien |
| 22 | Familie und Freunde | Familienbezeichnungen, の-Partikel |
| 23 | Erste Kanji (Zahlen + Natur) | 一二三四五六七八九十日月火水木金土 |
| 24 | N5-Zusammenfassung | Wiederholung + Prüfungsvorbereitung |

#### Kurs 3: N4 — Elementar
| # | Lektion | Inhalt |
|---|---------|--------|
| 25-36 | Fortgeschrittene Grammatik, Te-Form, Verbindungen, Höflichkeitsformen, etc. |

#### Kurs 4: N3 — Mittelstufe
#### Kurs 5: N4-N3 Thematische Vertiefung
(Hier können die bestehenden 36 thematischen Lektionen überarbeitet und eingeordnet werden)

### Bestehende Lektionen einordnen

Die 36 bestehenden thematischen Lektionen (Reisen, Kochen, Slang, etc.) passen am besten als **Vertiefungslektionen ab N4/N3**, wenn die Grundlagen sitzen. Vorgeschlagene Zuordnung:

| JLPT-Level | Bestehende Lektionen |
|---|---|
| N4 | Einkaufen, Essen, Familie, Verkehr, Wetter, Hobbys |
| N3 | Reisen, Wohnen, Gesundheit, Schulsystem, Feste, Natur |
| N3-N2 | Geschäftsjapanisch, Politik, Popkultur, Slang, Keigo |
| N2 | Literatur, Dialekte, Debatten, Karriere, Umwelt |

---

## 4. API-Entscheidungen (Zusammenfassung)

| Bereich | Entscheidung | Status |
|---|---|---|
| **Text-KI** | Gemini 3 Flash ($0.50/$3.00 pro 1M Tokens) | ✅ Bestätigt |
| **Bild-KI** | Flux 1.1 Pro ($0.04/Bild) oder gpt-image-1-mini ($0.036) | ⏳ Test nötig |
| **Speech/TTS** | Google Cloud TTS WaveNet (SSML/IPA, Gratis-Tier reicht) | ✅ Bestätigt |

Details: Siehe `RECHERCHE_BILD_APIS.md` und `RECHERCHE_SPEECH_APIS.md`

---

## 5. Technische Umsetzung (aktualisiert)

### Phase 1: Prototyp (Woche 1)
- [ ] `ai_services.py`: Gemini 2.5 Pro → Gemini 3 Flash umstellen
- [ ] VOICEVOX lokal installieren und testen
- [ ] Bild-API testen: 3 Vergleichsbilder (Flux / gpt-image-1-mini / aktuell)
- [ ] **Lektion 1 komplett als Prototyp** generieren (siehe `KONZEPT_PREMIUM_LEKTIONEN.md`)
- [ ] Neue Content-Typen im Frontend: `dialogue`, `word_breakdown`

### Phase 2: Pipeline + Lektionen 1-6 (Woche 2)
- [ ] Generierungs-Pipeline für Premium-Format aufbauen
- [ ] Audio-Integration (VOICEVOX) in Pipeline einbauen
- [ ] Lektionen 1-6 (Hiragana + erste Schritte) generieren
- [ ] Qualitätskontrolle: Nur bekannte Wörter verwendet?

### Phase 3: Lektionen 7-12 + Polish (Woche 3)
- [ ] Lektionen 7-12 (Katakana + Restaurant + Kanji) generieren
- [ ] Frontend-Anpassungen (Dialog-Ansicht, Audio-Player, Wort-Aufschlüsselung)
- [ ] Alte Lektionen archivieren (nicht löschen)
- [ ] Kursstruktur in DB anlegen

---

## 6. Offene Fragen

1. **Hauptfigur?** "Yuki" oder der Lernende selbst?
2. **Gate-Keeping?** Strikt (80% Quiz nötig) oder weich (Empfehlung)?
3. **Alte Lektionen?** Archivieren, als Bonus behalten, oder löschen?
4. **Handschrift-Übungen?** Für Hiragana/Katakana/Kanji? (Phase 2+)
5. **Bild-Stil?** Einheitlich Anime/Manga?

---

## 7. Dokumenten-Index

| Datei | Inhalt |
|---|---|
| `REFACTORING_PLAN.md` | Dieses Dokument — Gesamtübersicht |
| `KONZEPT_PREMIUM_LEKTIONEN.md` | Neues Lektionsdesign, Aufbau, 12-Lektionen-Plan |
| `RECHERCHE_JAPANISCH_DIDAKTIK.md` | JLPT-Struktur, Lernmethoden, Lehrbuch-Referenzen |
| `RECHERCHE_BILD_APIS.md` | Vergleich von 10 Bild-Generierungs-APIs |
| `RECHERCHE_SPEECH_APIS.md` | Vergleich von 12 TTS-APIs für Japanisch |
