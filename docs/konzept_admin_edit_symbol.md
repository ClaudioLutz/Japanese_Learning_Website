# Konzept: Admin-Bearbeitungs-Symbol auf öffentlichen Seiten

**Datum:** 2026-04-10  
**Status:** Entwurf  
**Ziel:** Eingeloggte Admins sehen auf jeder öffentlichen Seite ein schwebendes Symbol, das direkt zur passenden Admin-Verwaltungsseite verlinkt.

---

## 1. Problemstellung

Aktuell muss ein Admin, der auf einer öffentlichen Seite (z.B. Lektionsansicht, Kursübersicht) einen Fehler bemerkt oder Inhalte ändern möchte, manuell über die Navbar zum Admin-Panel navigieren und dort die richtige Seite/Lektion suchen. Das kostet Zeit und unterbricht den Arbeitsfluss.

## 2. Lösung: Floating Admin-Edit-Button

Ein **schwebendes Zahnrad/Stift-Symbol** wird auf jeder öffentlichen Seite eingeblendet — nur sichtbar für Admins. Ein Klick darauf führt direkt zur entsprechenden Admin-Verwaltungsseite mit Kontext (z.B. die richtige Lektion ist bereits fokussiert).

## 3. Betroffene Seiten und Ziel-Links

| Öffentliche Seite | Template | Route | Admin-Zielseite | URL-Parameter |
|---|---|---|---|---|
| Lektionsansicht | `lesson_view.html` | `/lessons/<id>` | Lektions-Editor | `/admin/manage/lessons?focus=<lesson_id>` |
| Kursansicht | `course_view.html` | `/course/<id>` | Kurs-Verwaltung | `/admin/manage/courses?focus=<course_id>` |
| Lektionsliste | `lessons.html` | `/lessons` | Lektions-Verwaltung | `/admin/manage/lessons` |
| Kursliste | `courses.html` | `/courses` | Kurs-Verwaltung | `/admin/manage/courses` |
| Meine Lektionen | `my_lessons.html` | `/my-lessons` | Lektions-Verwaltung | `/admin/manage/lessons` |
| Startseite | `index.html` | `/` | Admin-Dashboard | `/admin/` |

## 4. Technischer Ansatz

### 4.1 Variante A: Zentraler Block in `base.html` (empfohlen)

Ein neuer Block wird direkt in `base.html` eingefügt, sodass alle Seiten automatisch das Symbol erben. Jedes Child-Template kann den Ziel-Link über eine Template-Variable (`admin_edit_url`) steuern.

**Vorteil:** Einmalige Implementierung, automatisch auf allen Seiten aktiv.  
**Nachteil:** Child-Templates müssen `admin_edit_url` setzen, damit der Link kontextbezogen ist.

#### Umsetzung in `base.html` (nach Zeile 195, vor `</div>`):

```html
{% if current_user.is_authenticated and current_user.is_admin %}
<a href="{{ admin_edit_url or url_for('routes.admin_index') }}"
   class="admin-floating-edit"
   title="Diese Seite im Admin bearbeiten">
    <i class="fas fa-pencil-alt"></i>
</a>
{% endif %}
```

#### CSS (in `base.html` oder separates Stylesheet):

```css
.admin-floating-edit {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1050;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #f59e0b;           /* Amber — hebt sich ab, stört nicht */
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    transition: background 0.2s, transform 0.2s;
    text-decoration: none;
}
.admin-floating-edit:hover {
    background: #d97706;
    transform: scale(1.1);
    color: #fff;
    text-decoration: none;
}
```

#### In jedem Child-Template die Variable setzen:

```html
{# lesson_view.html #}
{% set admin_edit_url = url_for('routes.admin_manage_lessons') + '?focus=' + lesson.id|string %}

{# course_view.html #}
{% set admin_edit_url = url_for('routes.admin_manage_courses') + '?focus=' + course.id|string %}

{# lessons.html #}
{% set admin_edit_url = url_for('routes.admin_manage_lessons') %}

{# courses.html #}
{% set admin_edit_url = url_for('routes.admin_manage_courses') %}
```

### 4.2 Variante B: Eigener Block pro Template

Jedes Template definiert sein eigenes Admin-Symbol individuell. Mehr Kontrolle pro Seite, aber redundanter Code.

**Nicht empfohlen** — Variante A ist wartbarer.

### 4.3 Variante C: Tooltip-Menü mit mehreren Links

Statt eines einzelnen Links zeigt das Symbol beim Hover ein kleines Menü mit mehreren Optionen (z.B. "Lektion bearbeiten", "Content verwalten", "Seiten verwalten"). Umsetzbar mit Alpine.js, das bereits geladen ist.

**Geeignet als spätere Erweiterung** — für V1 reicht ein Direkt-Link.

## 5. Empfohlene Implementierung (Variante A, Detail)

### 5.1 Dateien die geändert werden

| Datei | Änderung |
|---|---|
| `app/templates/base.html` | Floating-Button + CSS einfügen (nach Zeile 195) |
| `app/templates/lesson_view.html` | `{% set admin_edit_url = ... %}` am Anfang |
| `app/templates/course_view.html` | `{% set admin_edit_url = ... %}` am Anfang |
| `app/templates/lessons.html` | `{% set admin_edit_url = ... %}` am Anfang |
| `app/templates/courses.html` | `{% set admin_edit_url = ... %}` am Anfang |
| `app/templates/my_lessons.html` | `{% set admin_edit_url = ... %}` am Anfang |

### 5.2 Keine Backend-Änderungen nötig

Die Admin-Check-Logik (`current_user.is_admin`) existiert bereits in `base.html` und funktioniert auf allen Seiten. Es sind keine neuen Routen, Models oder Services erforderlich.

### 5.3 `?focus=`-Parameter in Admin-Seiten

Die Admin-Templates (`manage_lessons.html`, `manage_courses.html`) nutzen bereits JavaScript für die Lektions-/Kursliste. Der `?focus=`-Parameter kann mit wenigen Zeilen JS ausgelesen werden, um das entsprechende Element zu highlighten und in den sichtbaren Bereich zu scrollen:

```javascript
// In manage_lessons.html (JS-Bereich)
const params = new URLSearchParams(window.location.search);
const focusId = params.get('focus');
if (focusId) {
    // Lektion in der Liste finden, scrollen, highlighten
    const row = document.querySelector(`[data-lesson-id="${focusId}"]`);
    if (row) {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        row.classList.add('highlight-flash');
    }
}
```

## 6. Design-Überlegungen

- **Position:** Unten rechts (fixed), da dort kein bestehendes UI-Element liegt
- **Farbe:** Amber (#f59e0b) — sichtbar aber nicht störend, passt zum bestehenden Admin-Button-Stil
- **Nur für Admins:** `{% if current_user.is_admin %}` — keine Sichtbarkeit für normale User
- **Mobile:** Button bleibt sichtbar, evtl. etwas kleiner (40x40px bei `max-width: 768px`)
- **Accessibility:** `title`-Attribut + `aria-label` für Screenreader
- **Kein Einfluss auf SEO/Performance:** Nur HTML+CSS, kein zusätzlicher API-Call

## 7. Aufwandsschätzung

- **base.html:** ~15 Zeilen (HTML + CSS)
- **5 Child-Templates:** Je 1 Zeile (`{% set admin_edit_url %}`)
- **Admin-Seiten (focus-Parameter):** ~10 Zeilen JS pro Seite (optional, Verbesserung)
- **Gesamt:** Kleine Änderung, kein Risiko, keine Migration nötig

## 8. Spätere Erweiterungen (optional)

1. **Tooltip-Menü** (Variante C): Hover zeigt Untermenü mit "Lektion bearbeiten", "Content verwalten", "Seiten verwalten"
2. **Inline-Edit-Modus**: Admin kann direkt auf der öffentlichen Seite Texte bearbeiten (HTMX + API)
3. **Seitenspezifischer Kontext**: Bei Lektionsseiten mit Seiten-Navigation direkt zur richtigen Seite im Editor verlinken
4. **Tastenkürzel**: z.B. `E` drücken öffnet den Admin-Editor (nur für Admins, via `window.currentUser.isAdmin`)
