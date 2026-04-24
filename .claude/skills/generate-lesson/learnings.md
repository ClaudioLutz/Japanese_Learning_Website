# Learnings — generate-lesson

Selbstverbesserndes Log. Wird vor jedem Run gelesen, nach jedem Run angehängt.

## Format

```markdown
## YYYY-MM-DD HH:MM — [JLPT-Level] Thema (Lesson ID X)

### Erfolge
- ...

### Probleme / Erkenntnisse
- Beobachtung → **Regel für nächstes Mal: ...**

### Aktuelle Regeln (kumulativ, wichtigste zuerst)
1. ...
2. ...
```

**Regel-Hochstufung:** Wenn derselbe Fehler 2× in unterschiedlichen Runs auftritt, **in SKILL.md §3 oder §5 hochheben**, nicht nur hier stehen lassen.

---

## Initial-Regeln (vor erstem Run, aus improve-jpl + CLAUDE.md abgeleitet)

1. **Mayuko-First:** Vor jeder Design-Entscheidung: "Würde Mayuko das bemerken, verstehen, wiederkommen?" Wenn nein → zurückstellen.
2. **Anfänger-Only:** N5 und N4. N3+ ist aktuell aus-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.** Niemals. Auch nicht "nur diesmal".
4. **Instruction-Language default `german`.** Mayukos Sprache.
5. **Beispielsätze dürfen KEINE Kanji/Vokabeln über dem Lektions-Level nutzen.** Wenn unvermeidbar: Hiragana schreiben.
6. **Umlaute echt, nicht ASCII-Fallback.** Schüler, nicht Schueler.
7. **Duplicate-Check vor Kana/Kanji/Vocabulary/Grammar-Insert.** Bestehende ID wiederverwenden.
8. **Atomare Transaktion:** Ganze Lektion oder nichts. Kein halbes Insert.
9. **Verifikation via Playwright ist Pflicht** bevor Git-Commit oder is_published=True.
10. **Mix der Quiz-Typen pro Page:** Nicht 10× multiple_choice. Immer mind. 2 Typen mischen (mc/tf/matching).

---

## Run-Log

<!-- Neuste Einträge oben, älteste unten. -->

_(Noch keine Runs. Erster Eintrag wird nach erstem `/generate-lesson` angehängt.)_
