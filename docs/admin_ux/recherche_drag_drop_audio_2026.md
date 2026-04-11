# Admin-UX Recherche: Drag-&-Drop, Audio-Aufnahme & State-of-the-Art Bearbeitung

**Datum:** 2026-04-11
**Kontext:** Japanese Learning Website — Admin-Panel Effizienz-Upgrade
**Ziel:** Admin-Bearbeitung von Lessons, Pages und Content so einfach, schnell und benutzerfreundlich wie moeglich machen. Plus: Audio-Aufnahme direkt im Browser fuer native TTS-Alternativen.

---

## 1. Bestandsaufnahme (Ist-Zustand)

### 1.1 Sortierung — aktuell nur Button-basiert (▲▼)

| Ebene | Modell-Feld | UI | API-Endpoint |
|---|---|---|---|
| **Lesson** (global) | `Lesson.order_index` ([app/models.py:174](../../app/models.py#L174)) | Buttons ▲▼ in [manage_lessons.html:70-73](../../app/templates/admin/manage_lessons.html#L70-L73) | `POST /api/admin/lessons/<id>/move` ([routes.py:1269-1320](../../app/routes.py#L1269-L1320)) |
| **LessonPage** | `LessonPage.page_number` (unique per Lesson) ([models.py:361](../../app/models.py#L361)) | **Keine Reorder-UI** — nur Add/Delete | `PUT /api/admin/lessons/<id>/pages/<page_num>` |
| **LessonContent** | `LessonContent.order_index` + `page_number` ([models.py:380-381](../../app/models.py#L380-L381)) | Buttons ▲▼ in [_js_pages.html:152-154](../../app/templates/admin/lessons/_js_pages.html#L152-L154) | `POST /api/admin/lessons/<id>/content/<content_id>/move` ([routes.py:1529-1584](../../app/routes.py#L1529-L1584)) |
| **QuizQuestion / QuizOption** | `order_index` ([models.py:480, 496](../../app/models.py#L480)) | Keine Reorder-UI | — |

**Probleme:**
- Jeder Klick = ein HTTP-Roundtrip. Bei 45 Vocab-Items auf einer Page ist "Item 45 nach oben" frustrierend.
- Keine Reorder-Moeglichkeit fuer Pages (nur Loeschen + Neu anlegen).
- Keine visuelle Vorschau beim Verschieben.
- Keine Mehrfach-Auswahl / Bulk-Move.
- `page_number` hat **keinen Auto-Renumber** beim Loeschen → Luecken moeglich.

### 1.2 Audio — nur Datei-Upload, keine Aufnahme

- **Upload:** `POST /api/admin/upload-file` ([routes.py:3370-3433](../../app/routes.py#L3370-L3433))
- **Formate:** MP3, WAV, OGG, AAC, M4A (bis 100 MB) ([_js_file_upload.html:9-10](../../app/templates/admin/lessons/_js_file_upload.html#L9-L10))
- **Preview:** Native `<audio controls>` ([_js_content.html:152](../../app/templates/admin/lessons/_js_content.html#L152))
- **Keine MediaRecorder-Integration.** Lehrer muessen extern aufnehmen, exportieren, hochladen.

---

## 2. Drag-&-Drop — State of the Art 2026

### 2.1 Library-Vergleich

| Library | Groesse | Framework-Pflicht | Nested | Multi-Container | Mobile/Touch | Integration-Aufwand |
|---|---|---|---|---|---|---|
| **SortableJS** | ~11 KB gz | keine | ✅ (via `group`) | ✅ (`group: name`) | ✅ nativ | ⭐ sehr gering |
| **Alpine Sort Plugin** (`@alpinejs/sort`) | +SortableJS | Alpine.js | ✅ | ✅ | ✅ | ⭐ sehr gering — Declarative |
| **dnd-kit** | ~30 KB gz | React | ✅ | ✅ | ✅ | ⭐⭐⭐ hoch — viel Setup |
| **Dragula** | ~6 KB gz | keine | ⚠️ eingeschraenkt | ✅ | ⚠️ | ⭐⭐ |
| **native HTML5 DnD** | 0 KB | keine | ✅ | ✅ | ❌ kein Touch | ⭐⭐⭐⭐ sehr hoch |

### 2.2 Empfehlung: **Alpine Sort Plugin** (= SortableJS unter der Haube)

**Warum:**
1. **Alpine.js ist bereits geladen** (siehe [base_admin.html](../../app/templates/admin/base_admin.html)).
2. **Declarative Syntax** passt zum Rest des Admin-UIs:
   ```html
   <ul x-sort="handleReorder($item, $position)" x-sort:group="content-items">
     <template x-for="item in items" :key="item.id">
       <li x-sort:item="item.id" x-sort:handle>...</li>
     </template>
   </ul>
   ```
3. **Cross-List** (Pages ↔ Pages, Content ↔ Content) out-of-the-box ueber `x-sort:group`.
4. **Drag-Handles** moeglich (`x-sort:handle`) — verhindert versehentliches Verschieben.
5. **Minimaler Bundle-Zuwachs** (~15 KB gzip).
6. **Touch/Mobile** nativ unterstuetzt.

**Alternative:** Pure SortableJS direkt einbinden, wenn Alpine-Plugin zu starr ist (z.B. fuer Multi-Drag-Select).

### 2.3 Konkrete Einsatzstellen

| # | Bereich | Heute | Ziel |
|---|---|---|---|
| **1** | Lessons-Liste (`manage_lessons.html`) | Buttons ▲▼ | Drag-Handle links, pro Zeile. Optional: Gruppierung nach Kategorie mit Cross-Group-Drag. |
| **2** | LessonPages (Tabs/Akkordeon) | Kein Reorder | Pages in Kanban-artiger Horizontal-Leiste oder vertikalem Akkordeon, per Drag sortierbar. |
| **3** | LessonContent pro Page | Buttons ▲▼ | Drag-Handle (`::`-Icon) links, Ghost-Preview, optional Multi-Select (Shift/Ctrl+Klick → Bulk-Move). |
| **4** | Content zwischen Pages verschieben | Keine UI | Drag von Page-Panel in anderes Page-Panel (via `x-sort:group="content-cross-page"`). |
| **5** | QuizOptions innerhalb QuizQuestion | Keine UI | Kleine Drag-Liste im Quiz-Editor. |

### 2.4 Backend-Aenderungen

**Problem heute:** `/move` macht Einzelschritt (one-up / one-down). Das ist inkompatibel mit Drag-&-Drop, weil der Ziel-Index beliebig ist.

**Loesung:** Neuer **Reorder-Bulk-Endpoint**:

```python
POST /api/admin/lessons/<lesson_id>/content/reorder
Body: { "page_number": 1, "ordered_ids": [12, 7, 3, 19, 5, ...] }
```

Vorteile:
- **Ein Request** statt N Einzelschritte.
- **Atomar** — SQLAlchemy-Transaction; bei Fehler Rollback.
- **Idempotent** — funktioniert bei doppelten PUT-Calls gleich.
- **Optimistic UI** — Frontend rendert sofort, Backend bestaetigt.

Analog fuer:
- `POST /api/admin/lessons/reorder` (globale Lesson-Order)
- `POST /api/admin/lessons/<id>/pages/reorder`
- `POST /api/admin/lessons/<id>/content/move-to-page` (Cross-Page-Move)

**Auto-Renumber-Helper** fuer Pages einbauen, damit Luecken geschlossen werden.

### 2.5 Visuelle / Interaktions-Details

- **Drag-Handle** links: `⋮⋮` Icon (Heroicons `bars-3`) — nur dort laesst sich dragen, Rest der Zeile bleibt klickbar (wichtig fuer Inline-Edit).
- **Ghost-Preview** mit `opacity: 0.4`, `transform: scale(0.98)`.
- **Drop-Placeholder**: 2-px blaue Linie zwischen Items (Tailwind `border-zen-indigo`).
- **Animation:** 150ms ease-out ueber `x-sort:config="{ animation: 150 }"`.
- **Feedback:** Toast "Reihenfolge gespeichert" **erst nach Backend-Bestaetigung**. Bei Fehler: Auto-Revert + Error-Toast.
- **Undo-Button** im Toast (5 Sekunden aktiv) — entspricht Bulk-Action-Best-Practice.
- **Keyboard-Alternative:** Fokussierter Handle + `Alt+↑/↓` = ein Schritt hoch/runter (Accessibility).

---

## 3. Audio-Aufnahme im Browser — MediaRecorder API

### 3.1 Warum selbst aufnehmen?

- **TTS-Alternative:** Lehrer koennen **native japanische Sprecherinnen** direkt im Admin aufnehmen, um den OpenAI-TTS (`nova`) zu ersetzen.
- **Qualitaet:** Menschliche Aufnahme > synthetisch, besonders bei Pitch-Akzenten.
- **Kosten:** Keine API-Calls pro Wiedergabe.
- **Workflow-Vereinfachung:** Kein externes Tool (Audacity, o.ae.) mehr noetig.

### 3.2 Technik-Stack

| Komponente | Rolle | Hinweis |
|---|---|---|
| **`navigator.mediaDevices.getUserMedia`** | Mikrofon-Zugriff | Braucht HTTPS oder localhost. |
| **`MediaRecorder`** | Aufnahme | Native API, Chrome/Firefox/Safari (ab 14.1). |
| **`MediaRecorder.isTypeSupported()`** | Format-Check | Vor Recording pruefen. |
| **Aufnahmeformat** | `audio/webm;codecs=opus` (Chrome/FF) oder `audio/mp4` (Safari) | Kein natives MP3/WAV im Browser! |
| **Upload** | `FormData` → `POST /api/admin/upload-audio-recording` | Bestehender Upload-Handler wiederverwendbar. |
| **Transcoding** | Server-seitig **optional** (ffmpeg → mp3) | Webm/Opus funktioniert in allen modernen Browsern fuer Playback, Transcoding ist nur noetig, wenn Safari-Support < 14.5 wichtig ist. |
| **Waveform-Visualisierung** | **wavesurfer.js** v7+ mit `Record`-Plugin | Live-Waveform waehrend Aufnahme, Playback, Regions. |
| **Trim / Cut** | **nicht** in wavesurfer nativ | Optional: audio buffer slice via Web Audio API, oder server-seitig via ffmpeg-python. |

### 3.3 Empfohlener Flow im Admin-UI

```
┌─────────────────────────────────────────────────┐
│  Audio-Content hinzufuegen                      │
├─────────────────────────────────────────────────┤
│  ○ Datei hochladen    ● Direkt aufnehmen        │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  ████▁▁▃▅▇█▇▅▃▁  Live-Waveform            │  │
│  │                                           │  │
│  │  ● REC  ■ Stop  ▶ Play  ↻ Retake          │  │
│  │                                           │  │
│  │  00:03.42 / 00:30.00                      │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  [ Abbrechen ]          [ Speichern & Zuweisen ] │
└─────────────────────────────────────────────────┘
```

**Features:**
- **Max-Dauer** (z.B. 30s pro Item) mit Countdown.
- **Retake** ohne Server-Roundtrip.
- **Live-Waveform** (wavesurfer `RecordPlugin`).
- **Playback vor Upload** — Aufnahme anhoeren + verwerfen moeglich.
- **Auto-Naming:** `recording_<lesson_id>_<content_id>_<timestamp>.webm`.
- **Permission-Handling:** Bei `NotAllowedError` klarer Hinweis mit "Mikrofon aktivieren"-Anleitung.

### 3.4 Backend-Erweiterungen

**Neuer Endpoint:**

```python
POST /api/admin/audio/record-upload
Body: multipart/form-data
  - file: Blob (audio/webm)
  - content_id: int (optional)
  - lesson_id: int
  - duration_ms: int
```

Validierung:
- MIME-Check gegen Whitelist: `audio/webm`, `audio/ogg`, `audio/mp4`, `audio/mpeg`.
- Max-Size: 10 MB (Aufnahmen sind kleiner als Uploads).
- Dauer-Limit server-seitig (ffprobe).
- Optional: Auto-Transcoding zu MP3 via `ffmpeg-python`.

**Empfehlung:** Kein Transcoding in V1. Webm/Opus funktioniert in allen modernen Browsern und ist ~50% kleiner als MP3.

### 3.5 Library-Wahl

| Option | Pro | Contra |
|---|---|---|
| **Vanilla MediaRecorder + wavesurfer.js Record Plugin** | Kein Extra-Aufwand, bewaehrt, 0 Dependencies ausser wavesurfer | — |
| **RecordRTC** | Mehr Features (pause, multistream) | Groesser, unnoetig fuer Single-Track-Voice |
| **Opus-media-recorder (Polyfill)** | Safari < 14.5 Support | Heute kaum noetig |

→ **wavesurfer.js v7 + Record-Plugin** ([wavesurfer.xyz](https://wavesurfer.xyz/)) gewaehlt.

---

## 4. Weitere State-of-the-Art Admin-UX Patterns 2026

### 4.1 Inline-Editing (bereits teilweise vorhanden)

- **Pattern:** Feld mit Hover-Pencil → Klick fokussiert Inline-Input → Blur = Auto-Save.
- **Vorteil:** Kein Modal-Overhead fuer Kleinigkeiten (Titel, order_index).
- **Existiert bereits** fuer Vocabulary/Kanji in Content-Editor — **ausweiten** auf:
  - Lesson-Titel direkt in Tabelle
  - Page-Name direkt in Tab-Leiste
  - Content-Title in Content-Liste
- **Save-Hints:** Gruener Haken fuer 1s nach Save, roter Rand bei Fehler.

### 4.2 Bulk-Actions

**Heute:** Keine.

**Ziel:**
- **Checkbox-Spalte** in Lessons-/Content-Tabellen.
- **Sticky Action-Bar** erscheint oben, wenn >= 1 selektiert:
  - Bulk-Delete (mit Confirm)
  - Bulk-Move (neue Page / neue Lesson)
  - Bulk-Publish/Unpublish
  - Bulk-Export als JSON/CSV
- **Select-All / Invert** Checkbox im Header.
- **Shift+Klick = Range-Select** (wie Gmail).
- **Ctrl/Cmd+Klick = Multi-Select**.
- **Undo-Toast** nach jeder Bulk-Action (5s Fenster, rueckgaengig per localStorage-Snapshot).

### 4.3 Keyboard-First Workflows

Admin-UX 2026 Prinzip: "Power-User tun die gleiche Sache 100x pro Tag — Tastatur regiert".

**Bestehende Command Palette** (`Ctrl+K`) **erweitern** um:

| Shortcut | Aktion |
|---|---|
| `Ctrl+K` | Command Palette (existiert) |
| `N` | Neue Lesson |
| `G` dann `L` | Go to Lessons |
| `G` dann `C` | Go to Courses |
| `G` dann `K` | Go to Kanji |
| `/` | Fokus auf Search-Feld |
| `E` auf Row | Edit Row |
| `Delete` auf Row | Delete (mit Confirm) |
| `Alt+↑` / `Alt+↓` | Row nach oben/unten |
| `Space` | Row selektieren (bulk) |
| `?` | Shortcut-Overlay anzeigen |

**Wichtig:** Shortcuts **deaktivieren**, waehrend User im Input-Feld tippt.

### 4.4 Daten-Tabellen Best Practices

- **Sticky Header** beim Scrollen.
- **Frozen Columns** (Title + Actions) bei breiten Tabellen.
- **Spalten-Resize** + **Column-Show/Hide-Menue**.
- **Virtualisierung** ab 200+ Zeilen (z.B. mit `tanstack/virtual` vanilla).
- **Filter-Chips** statt Dropdowns (per Klick aktiv/inaktiv).
- **Quick-Filter** aus URL-Params (Bookmarks funktionieren).
- **Pagination** mit "Jump to Page" fuer grosse Datenmengen.

### 4.5 Autosave & Optimistic UI

- **Drafts:** Lesson/Page-Editor speichert alle 5s in localStorage — "Unsaved changes" Indikator.
- **Optimistic Updates:** Drag-Drop → UI aktualisiert **sofort**, Backend-Call im Hintergrund. Bei 4xx/5xx → Auto-Revert + Error-Toast.
- **Conflict-Detection:** `updated_at`-Timestamp mitschicken; 409 wenn jemand anderes geaendert hat.

### 4.6 Fehler-Vorbeugung

- **Soft-Delete** (30 Tage Papierkorb) statt Hard-Delete fuer Lessons.
- **Confirm-Dialoge** nur fuer irreversible / destructive Aktionen — nicht fuer alles.
- **Preview-Panel** rechts neben Editor (Live-Preview der Lesson-Seite).
- **Validierung inline** — rote Unterkringelung, nicht erst beim Submit.

### 4.7 Performance / Loading States

- **Skeleton-Loaders** statt Spinner.
- **HTMX Partials** fuer Teil-Updates (bereits im Stack).
- **Debounced Search** (300ms).
- **Infinite Scroll** optional statt Pagination (Content-Liste).

---

## 5. Konkreter Umsetzungs-Fahrplan

**Phase 1 — Drag-&-Drop Foundation** (hoechste Prioritaet, groesster Impact)
1. Alpine Sort Plugin einbinden (`@alpinejs/sort` via CDN).
2. Neue Reorder-API-Endpoints:
   - `POST /api/admin/lessons/reorder`
   - `POST /api/admin/lessons/<id>/pages/reorder`
   - `POST /api/admin/lessons/<id>/content/reorder` (mit `page_number`)
3. `manage_lessons.html` umbauen: Drag-Handles + Alpine-Sort fuer Lessons-Liste.
4. `_js_pages.html` / `_js_content.html` umbauen: Content pro Page draggable.
5. Cross-Page-Drag aktivieren (`group: "content"`).
6. Optimistic UI + Undo-Toast.

**Phase 2 — Page-Reorder + Inline-Edit**
7. LessonPages sortierbar machen (neue UI + API).
8. Inline-Edit fuer Lesson-Titel in Tabelle.
9. Auto-Renumber-Helper fuer page_number-Luecken.

**Phase 3 — Audio-Recording**
10. wavesurfer.js v7 + RecordPlugin einbinden.
11. Recording-UI in Content-Wizard ("Direkt aufnehmen" Tab).
12. Neuer Endpoint `/api/admin/audio/record-upload`.
13. MIME-Validierung + Max-Size 10 MB.
14. Permission-Handling + Error-States.

**Phase 4 — Bulk-Actions & Keyboard**
15. Checkbox-Spalte + Sticky Action-Bar.
16. Bulk-Delete, Bulk-Move, Bulk-Publish.
17. Keyboard-Shortcuts (Alt+↑/↓, E, N, /, ?).
18. Shortcut-Overlay (`?`).

**Phase 5 — Polish**
19. Soft-Delete mit Papierkorb.
20. Autosave Drafts.
21. Skeleton-Loaders.
22. Spalten-Config persistent in localStorage.

---

## 6. Offene Fragen fuer den User

1. **Audio-Format:** Webm/Opus als Speicherformat okay, oder MP3-Transcoding gewuenscht (Cloud-Run-Ressourcen?)?
2. **Soft-Delete:** Papierkorb implementieren, oder reicht Direkt-Delete mit Confirm?
3. **Phase-Prioritaet:** Stimmt die Reihenfolge (DnD zuerst, Audio danach), oder ist Audio-Recording wichtiger?
4. **Multi-Select Drag:** Nice-to-have oder Pflicht?
5. **Scope Cross-Page-Move:** Nur innerhalb einer Lesson, oder auch zwischen Lessons (waere zusaetzlicher Aufwand)?

---

## 7. Quellen

### Drag & Drop
- [Alpine.js Sort Plugin (offiziell)](https://alpinejs.dev/plugins/sort)
- [SortableJS GitHub](https://github.com/SortableJS/Sortable)
- [SortableJS Live Demo](https://sortablejs.github.io/Sortable/)
- [Puck: Top 5 Drag-&-Drop Libraries 2026](https://puckeditor.com/blog/top-5-drag-and-drop-libraries-for-react)
- [CSS-Script: 10 Best Drag-&-Drop Libraries 2026](https://www.cssscript.com/best-drag-drop-javascript-libraries/)
- [Desarrollolibre: SortableJS + Alpine Integration](https://www.desarrollolibre.net/blog/javascript/sortable-js-alpinejs-for-drag-and-drop-sorting-23)
- [Laravel News: Alpine Sort Plugin](https://laravel-news.com/alpine-sort-plugin)

### Audio Recording
- [MDN: MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [MDN: Using MediaStream Recording API](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream_Recording_API/Using_the_MediaStream_Recording_API)
- [Chrome Dev Blog: Record audio and video with MediaRecorder](https://developer.chrome.com/blog/mediarecorder)
- [wavesurfer.js offiziell](https://wavesurfer.xyz/)
- [wavesurfer.js Record Plugin Doku](https://deepwiki.com/katspaugh/wavesurfer.js/4.4-record-plugin)
- [Medium: Record Audio in JS and upload to Backend](https://franzeus.medium.com/record-audio-in-js-and-upload-as-wav-or-mp3-file-to-your-backend-1a2f35dea7e8)

### Admin-UX
- [Eleken: Bulk Action UX — 8 Guidelines](https://www.eleken.co/blog-posts/bulk-actions-ux)
- [FuseLab: Enterprise UX Guide 2026](https://fuselabcreative.com/enterprise-ux-design-guide-2026-best-practices/)
- [GlitchLabs: Admin Dashboard UX Patterns 2026](https://www.glitchlabs.app/insights/admin-dashboard-ux-patterns)
- [Pencil & Paper: Data Table Design Patterns](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables)
- [Medium: Keyboard Shortcuts UX Case Study](https://medium.com/@pratikkumar_10506/creating-dashboard-shortcuts-ux-case-study-c88f01985de0)
