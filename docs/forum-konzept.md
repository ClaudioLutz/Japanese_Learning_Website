# Benutzer-Forum — Konzept & Implementierungs-Spec

Stand: 2026-06-20 · Branch `worktree-forum` (von `origin/main`)

Recherche (Workflow-Fan-out: Datenmodell, Routen, Templates, Security, Tests, Best-Practices)
+ adversariale Verifikation. Ergebnis: **leichtgewichtiges, custom-gebautes Forum** unter
Wiederverwendung der vorhandenen Primitive (Flask-Login, SQLAlchemy 2.0, `markdown`/`bleach`,
flask-limiter, WTForms-CSRF, Design-System). **Kein Forum-Framework** (FlaskBB/Discourse) —
das würde ein zweites User-/Auth-Modell und fremde Templates erzwingen.

## Festgezurrte Entscheidungen

1. **Lesen ist login-pflichtig** (Mitglieder-/Feedback-Bereich). Vermeidet Soft-404/Thin-Content
   bei ~0 Nutzern und die Sitemap/noindex-Gymnastik. Forum-Routen sind **nicht** in `sitemap.xml`,
   in `robots.txt` unter `/forum` gesperrt.
2. **Migration strikt additiv** — nur `CREATE TABLE forum_*` (+ FK auf `user.id`). Keine Änderung
   an bestehenden Tabellen. (Prod-Container macht beim Start `flask db upgrade`.)
3. **Blueprint NICHT csrf-exempt.** WTForms-CSRF-Token in jedem POST-Form; AJAX (pin/lock/delete)
   via `X-CSRFToken`-Header aus dem `<meta name="csrf-token">`.
4. **Forum nicht in die Primary-Topnav** (max. 5 Daily-Loop-Items) → User-Dropdown (Desktop +
   Mobile; das Dropdown bleibt mobil sichtbar). Bottom-Nav bleibt bei 5 Items (kein Crowding).
5. **OP = erster Post** (eine `forum_post`-Tabelle, `is_op=True`). Ein einziger Edit-/Delete-/
   Render-Pfad statt divergierendem `Topic.body`.
6. **Soft-Delete** für Posts und Topics (`is_deleted`-Flag + `deleted_at`/`deleted_by_id`).
   Gelöschte Posts rendern als „[Beitrag gelöscht]", Zeile bleibt (Thread-Kohärenz).
7. **Moderation:** Admin pin/lock/delete (Topic); Nutzer editieren/löschen eigene Posts.
8. **Anti-Spam:** flask-limiter (Topic-Create 3/h, Reply 10/h, Edit 20/h), Key auf `user.id`
   gebunden (Cloudflare kollabiert IPs); WTForms `Length`-Validierung (Titel 5–200, Body 10–10000).
9. **Ankündigungen admin-only** serverseitig erzwungen via `ForumCategory.admin_only_post`-Flag.
10. **Slug** = `slugify(title)+"-"+id` (eigener dependency-freier Slugifier mit Umlaut-Translit).
    Topic-Lookup robust per `id`; Slug nur als lesbarer URL-Schmuck.
11. **N+1 vermeiden:** denormalisierter `reply_count` + `last_activity_at` auf dem Topic (atomar
    im selben Commit gepflegt) + `joinedload(author)` in Listen.
12. **v1-YAGNI:** keine Notifications, Mentions, Reactions, Volltext-Suche, Read/Unread, Reporting.

## Datenmodell (`app/models.py`, SQLAlchemy-2.0-`Mapped`-Stil)

- **ForumCategory**: `id, name, slug(unique), description, icon, display_order, admin_only_post,
  is_active, created_at`. → `topics`-Relationship.
- **ForumTopic**: `id, category_id→forum_category, author_id→user, title, slug, is_pinned,
  is_locked, is_deleted, view_count, reply_count, created_at, last_activity_at, deleted_at,
  deleted_by_id`. Sortierung `is_pinned DESC, last_activity_at DESC`. Indizes auf
  `category_id, author_id, last_activity_at, created_at`.
- **ForumPost**: `id, topic_id→forum_topic, author_id→user, body(Text), is_op, is_deleted,
  created_at, edited_at, deleted_at, deleted_by_id`. Index auf `topic_id, created_at`.

FK-Ziel ist `user.id` (Tabelle `user`, **nicht** `users`).

## Routen (`app/forum_routes.py`, Blueprint `forum`, Prefix `/forum`)

| Methode | Pfad | Endpoint | Auth | Limit |
|---|---|---|---|---|
| GET | `/forum/` | `forum.index` | login | – |
| GET | `/forum/<category_slug>` | `forum.category` | login | – |
| GET/POST | `/forum/<category_slug>/new` | `forum.new_topic` | login (+admin bei admin_only) | 3/h |
| GET | `/forum/topic/<int:topic_id>[/<slug>]` | `forum.view_topic` | login | – |
| POST | `/forum/topic/<int:topic_id>/reply` | `forum.reply` | login | 10/h |
| GET/POST | `/forum/post/<int:post_id>/edit` | `forum.edit_post` | login (Autor/Admin) | 20/h |
| POST | `/forum/post/<int:post_id>/delete` | `forum.delete_post` | login (Autor/Admin) | – |
| POST | `/forum/topic/<int:topic_id>/pin` | `forum.pin_topic` | admin | – |
| POST | `/forum/topic/<int:topic_id>/lock` | `forum.lock_topic` | admin | – |
| POST | `/forum/topic/<int:topic_id>/delete` | `forum.delete_topic` | admin | – |

Pagination: Topics 20/Seite, Posts 15/Seite (`.paginate(error_out=False)`).

## Security

- **XSS:** Body via neuem Jinja-Filter `forum_markdown` (markdown→bleach, **ohne `span`**,
  `linkify` mit `nofollow`+`target_blank`). Titel nur Jinja-Autoescape (`| e`), nie Markdown.
- **CSRF:** WTForms-Token in Forms; AJAX via Header. Blueprint nicht exempt.
- **Lock:** gesperrtes Topic → kein Reply/Edit (ausser Admin), `abort(403)`/Flash.
- **Autorisierung:** `_require_post_author_or_admin` → `abort(403)`.
- **Soft-Delete-Lookup:** alle Reads filtern `is_deleted=False`; gelöschtes Topic → 404.

## Templates (`app/templates/forum/`, ink-on-washi, Dark-Mode-parat)

`_forum_base.html` (erbt `base.html`, lädt forum-CSS im `styles`-Block, isoliert von `custom.css`
→ kein Deck-Karussell-Risiko), `index.html`, `category.html`, `topic.html`, `new_topic.html`,
`edit_post.html`. Eigene `forum-*`-Klassen mit Tokens (`--card-background`, `--text-color`,
`--shu` nur für den Primär-CTA), **kein Bootstrap `.card`** (zwingt im Dark dunklen Text).

## Tests (`tests/integration/test_forum.py`)

conftest: sqlite-in-memory + `create_all` → Forum-Tabellen automatisch. Fixtures `auth_client`,
`admin_client` (Tuple `(client, user)`). Factories in `tests/factories.py`. Abdeckung: Login-Gate,
Create/Reply/Edit/Delete (soft), Lock verhindert Reply, Autor/Admin-Autorisierung, Ankündigungen
admin-only, Pagination, 404, Slug-Format.

## Seed

`scripts/seed_forum_categories.py` — idempotent (upsert per slug): Ankündigungen (admin_only),
Vorschläge, Hilfe & Fragen, Off-Topic.
