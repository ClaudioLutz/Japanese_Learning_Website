# Marketing-Verbesserungsplan — japanese-learning.ch

**Erstellt:** 2026-05-31 · **Methode:** 8-köpfiges Marketing-Team (je Opus 4.8, 1 Disziplin), Lead-Synthese
**Scope:** Recherche + Priorisierung + Plan. **Keine Umsetzung in dieser Runde.**
**Grundlage:** Live-Site (Gast- + eingeloggte Ansicht, Desktop 1440 / Mobile 390, 20 Screenshots), Code-Review, Live-`curl`, Web-Benchmarks. **47 Findings** über 8 Disziplinen, hier dedupliziert.

> Hinweise: CH-Deutsch (ss statt ß). Preise CHF. „Mayuko" ist intern und darf **nie** als öffentliches Verkaufsargument auftreten (siehe Task **F5**). Quiz ohne `fill_in_the_blank`. Produktions-DB/Deploy werden in der Umsetzung separat behandelt.

---

## Kernbefund (Executive Summary)

Die Plattform ist **produkt- und retention-seitig stark** (strukturierter N5-Pfad, FSRS-SRS, Streaks/XP, 24 Achievements, exzellente Stats-Seite, saubere Marken-Optik, solide SEO-Basis). Der Engpass ist **nicht der Inhalt, sondern der Funnel und die Messbarkeit**:

1. **Blindflug:** Es gibt **kein Analytics/Tracking** (dreifach verifiziert). Jede Optimierung ist ohne Baseline ein Ratespiel → **Mess-Fundament zuerst.**
2. **Der teuerste Funnel-Moment verschweigt den Wert:** Gäste sehen auf Paywall **und** Bundle **weder Preis noch Garantie noch Zahlungs-Signale** — alles steckt hinter dem Login. 4-fach unabhängig bestätigt.
3. **Verifizierte Funnel-Lecks:** `register()` ignoriert `next` und loggt nicht automatisch ein (Doppel-Login am Kaufabschluss); „Kostenlos starten" führt in eine Liste statt in Inhalt; der heisseste Aktivierungsmoment (Vokal-Probe 5/5, Gratis-Lektion-Ende) endet **ohne** Call-to-Action bzw. ohne Erfolgserlebnis.
4. **Differenzierung vergraben:** Die belastbare Marktlücke (**auf Deutsch · einmal zahlen statt Abo · verstehen statt Lückentext-Raten**) steht nirgends above-the-fold — obwohl der ganze Wettbewerb Abo-getrieben und englischsprachig ist.
5. **Kein Aussenkanal:** Keine Lifecycle-Mails (nur Passwort-Reset), Web-Push ist toter Code → abgesprungene Nutzer sind permanent verloren. Grösster mittelfristiger Retention-Hebel.

**Faktische Eckdaten (live verifiziert):** Bundle Early-Bird **CHF 9.90** / regulär CHF 14.90 / Single CHF 5 / Lifetime; N5-Coverage real **38.5 % Vokabeln, 55 % Kanji** (80 %-Schwelle für Preiserhöhung also noch weit weg); 36 Lektionen (≈14 gratis); Wettbewerb: Duolingo Super ~$96/J, WaniKani $89/J ($299 Lifetime), Bunpro $50/J, Renshuu $50/J, Klubschule Migros ZH CHF 741 für **einen** A1-Teilkurs.

---

## Teil A — Priorisierte Shortlist (Impact-gerankt)

ICE = (Impact + Confidence + Ease) / 3, je 1–10 (Ease 10 = sehr leicht). Aufwand: S < ½ Tag · M ~1–3 Tage · L > 3 Tage.

| # | ID | Initiative | Stream | ICE | Aufwand | Warum (Kern) |
|---|----|-----------|--------|-----|---------|--------------|
| 1 | **A1** | Analytics-Fundament (Plausible, cookieless) + 12 Funnel-Events | A | **9.3** | S | Ohne Messung ist alles andere Blindflug; macht jeden Hebel bewertbar |
| 2 | **B1** | Gast sieht Preis/Garantie/Payment auf Paywall **+** Bundle | B | **8.7** | S | 4× bestätigter Conversion-Leak im stärksten Kaufmoment |
| 3 | **D1** | `register()` `next`-Fix + Auto-Login | D | **8.7** | S | Verifizierter Bug: Doppel-Login + Zielverlust am Kaufabschluss |
| 4 | **F3** | CH-Deutsch: „ß" → „ss" auf öffentlicher `/ueber` | F | **8.3** | S | „Swiss-made"-Versprechen wird vom reichsdeutschen ß gebrochen |
| 5 | **F1** | AGB an die beworbene 30-Tage-Garantie angleichen | F | **8.3** | S | Werbung widerspricht AGB → Glaubwürdigkeits- **und** Rechtsrisiko |
| 6 | **E3** | Vokal-Probe: animierter CTA bei 5/5 → erste Lektion | E | **8.3** | S | Heissester Mikro-Erfolg im Funnel verpufft ohne Button |
| 7 | **E2** | „Kostenlos starten" → direkt in erste Gast-Lektion | E | **8.0** | M | Klick → Lernen statt Klick → Liste → Scan → Klick |
| 8 | **B3** | Anti-Abo-Frame + Klubschule-Anker (CHF 741 vs 9.90) | B | **8.0** | S | Belastbare, web-belegte Marktlücke endlich am Kaufpunkt |
| 9 | **G1** | E-Mail-Lifecycle (Opt-in + Due-Reminder + Win-back) | G | **7.7** | M | Einziger Aussenkanal; grösster Retention-Hebel (EdTech 10–35 % Re-Engagement) |
| 10 | **D3** | Gast-Celebration + „Fortschritt sichern"-CTA am Lektionsende | D | **7.7** | M | Aha-Moment ist genau für die Sign-up-Zielgruppe deaktiviert |
| 11 | **A2** | Nav-Bundle-CTA Indigo → Marken-Shu + EIN Primär-CTA | A | **7.7** | S | Markenbruch + zwei konkurrierende Primär-CTAs schwächen Klickrate |
| 12 | **F2** | Founder-Gesicht (Foto + Signatur) auf `/ueber` + Mini-Badge | F | **7.7** | S/M | Stärkster ehrlicher Trust-Anker bei Solo-Anbieter ohne Testimonials |
| 13 | **E1** | Differenzierung above-the-fold (Deutsch · kein Abo · verstehen) | E | **7.7** | M | „Warum besser?" wird in 5 Sek. nicht beantwortet |
| 14 | **B4** | Zahlen-Konsistenz Home↔Bundle↔Über (eine „heute/Ziel"-Sprache) | B/E | **7.7** | S | Widersprüchliche Kernzahlen am Kaufpunkt = Misstrauen |
| 15 | **H1** | `/learn/n5` 301-Fragment → echte indexierbare N5-Hub-Seite | H | **7.7** | S/M | Generischste N5-URL verschenkt Ranking-Autorität (Pos. ~31) |
| 16 | **C1** | Bundle-Banner auf `/lessons` (No-Brainer-Anker) | C | **7.3** | S | Anker existiert nur auf der Paywall, nicht in der Hauptübersicht |
| 17 | **F4** | JLPT-Datum-Faktencheck `/jlpt-n5-schweiz` + Quelllink | F | **7.3** | S | Fixes UZH-Datum vermutlich falsch → E-E-A-T-Risiko |
| 18 | **A3** | Core Web Vitals: 7 Fremd-CDNs reduzieren/self-hosten | A | **7.0** | M | LCP-Killer auf Mobile; CWV ist Ranking-Faktor |
| 19 | **C2** | Single-Checkout ins Sumi-System + Bundle-Upsell | C | **7.0** | S/M | Bootstrap-Insel + verschwundener Upsell im Kaufmoment |
| 20 | **B8** | Preis-Anker nach oben („N5 + N4"-Stufe CHF 39–49) | B | **5.7*** | M | CHF 9.90 wirkt fast zu billig; oberer Anker hebt ARPU (*hoher strateg. Impact) |
| 21 | **H2** | Programmatic-SEO-Hub (~900 Long-Tail) + Ratgeber-Blog | H | **6.7*** | L | Grösste organische Wette; Nische unbesetzt (*I=9) |
| 22 | **G2** | Streak-UTC-Bugfix (Europe/Zurich) + Milestones | G | **6.7** | S | Streak kann bei späten CH-Sessions fälschlich brechen |

**Weitere aufgenommene Findings** (vollständig in Teil B, Streams B–H): B2 Early-Bird-Dringlichkeit · B5 „Doppelte Garantie"-Wording · B6 Bundle-Eyebrow · B7 Founder-Badge · C3 Gratis-Stufen-Analyse · D2 Register-Formular entschlacken · D4 Modul-CTA-Sackgasse · D5 Lesson-Interlinking + Course-Schema · D6 Feedback-Sammelmechanik · E4 Home-Zahlen · E5 Headline-A/B · E6 „Dein Start"-Strip + Mobile-Probe · F5 Mayuko-Anonymisierung · G3 Web-Push · G4 Wochen-Digest · G5 Daily-Challenge-Hook · G6 Achievement-Notify · G7 SRS-Empty-State · G8 Abo-Churn-Lifecycle · H3 robots/AI-Bots · H4 Modul-Slugs · A4 Brand-Subtag · A5 globale Events.

---

## Teil B — Workstreams (parallele Swimlanes)

**Designprinzip:** Jeder Stream besitzt **disjunkte Dateien** → mehrere Entwickler (idealerweise je 1 Git-Worktree) arbeiten gleichzeitig ohne Überschreibungen. Events (`window.plausible(...)`) fügt **jeder Stream in seinen eigenen Templates** ein — die Helper-Funktion kommt aus **A1**.

### Parallelitäts-/Konflikt-Matrix

| Stream | Primäre Dateien (exklusiv) | Parallel? | Koordinations-Hinweis |
|--------|----------------------------|-----------|------------------------|
| **A** Fundament | `base.html`, `static/js/*` | ✅ sofort | **A1 zuerst** — liefert `window.plausible()`-Helper (weiche Abhängigkeit für Event-Tasks in B/D/E) |
| **B** Pre-Login-Angebot | `lesson_paywall.html`, `n5_bundle.html`, `bundle_service.py` | ✅ | einziger Editor von `n5_bundle.html`/`bundle_service.py` |
| **C** Lessons-Liste/Checkout | `lessons.html`, `purchase.html` | ✅ | — |
| **D** Auth & Aktivierung | `routes.py` (auth/index/view_lesson), `register.html`, `forms.py`, `lesson_view.html`, `module_detail.html` | ✅ | **`routes.py` auch von H** → disjunkte Regionen, kleine Commits/Rebase oder H nach D |
| **E** Home-Messaging | `index.html` | ✅ | **D4** braucht eine Mini-Variable aus `routes.py` (D) → abstimmen |
| **F** Trust/Legal/Content | `ueber.html`, `agb.html`, `jlpt_n5_schweiz.html`, DB-Content | ✅ | **F5** ändert DB-Content (separat, mit Backup) |
| **G** Retention-Aussenkanal | `mail_service.py`, `models.py`, `sw.js`, `srs_routes.py`, `requirements.txt`, neue Cron + `templates/email/` | ✅ | einziger Editor von `models.py`/`mail_service.py` |
| **H** SEO/Organic | `seo_routes.py`, neues `content_routes.py` + Templates, `routes.py` (learn_path-Region) | ⚠️ mit D koordinieren | `routes.py`-Region disjunkt zu D; H2 ist die einzige L-Wette |

> **Reihenfolge-Empfehlung:** A1 starten (Welle 0). Dann B, C, D, E, F, G parallel (Welle 1). H parallel, aber `routes.py`-Touch mit D abstimmen. H2 ist eine eigenständige grössere Initiative (Welle 2).

---

### Stream A — Mess- & Performance-Fundament (`base.html`)

**A1 · Analytics-Fundament + 12 Funnel-Events** — ICE **9.3** · S · *keine Abhängigkeit (Voraussetzung für alle Event-Tasks)*
- **Problem:** Kein GA4/GTM/Plausible/Umami/Pixel/Matomo, kein dataLayer (3× verifiziert: Live-`curl`, Grep `app/`, `base.html`). Gesamter Funnel ist nicht messbar/A-B-testbar.
- **Impact:** Macht **alle** anderen Hebel messbar — Conversion-Rate je Funnel-Stufe, gezielte Drop-off-Behebung.
- **Skizze:** **Plausible** (cookieless, EU-Hosting → kein Consent-Banner nötig unter nDSG/DSGVO; GA4 verliert real ~44 % Traffic durch Consent-Refusal). Alternativ Umami self-hosted (passt zu Docker/Cloudflare). Ein `defer`-Script in `base.html`-`<head>` + `window.plausible()`-Helper. **12 Events:** `page_view`, `vowel_demo_played`, `sign_up`, `lesson_start`, `lesson_complete`, `paywall_view`, `bundle_view`, `checkout_start`, `purchase` (Wert als Prop), `review_session_start`, `streak_milestone`, `kana_game_played`.
- **Dateien:** `base.html` (Script + page_view + streak/kana-Events); übrige Events werden in den jeweiligen Stream-Templates abgefeuert.
- **Akzeptanz:** Live ein Event in Plausible sichtbar; `purchase` mit Betrag; keine Cookie-Banner-Reibung.

**A2 · Nav-Bundle-CTA Indigo → Shu + ein dominanter Primär-CTA** — ICE **7.7** · S
- **Problem:** `.topnav-link-cta` nutzt `#4f46e5` Indigo (`base.html:327-347`), Avatar-Gradient `#4f46e5→#2563eb` (`:417`) — Bruch des Sumi/Shu-Designsystems und farbliche Konkurrenz zum orangenen „Kostenlos starten" (`:223`).
- **Skizze:** Bundle-CTA als Shu-Outline/Ghost; gratis-CTA klar dominant; Bundle-Push erst nach erster Gratis-Lektion (Paywall/Bundle-Hint erledigen das).
- **Akzeptanz:** Genau ein dominanter Primär-CTA top-of-funnel; keine Indigo-Flächen ausserhalb der Marke.

**A3 · Core Web Vitals: Fremd-CDN-Diät** — ICE **7.0** · M
- **Problem:** Live lädt `/` Bootstrap 5.3.3 (CSS+JS), jQuery 3.6, FontAwesome 6.4, Alpine, confetti, sortablejs von 3 Fremd-Hosts — LCP-/Render-Block-Treiber (Framework-Mix Bootstrap+Tailwind).
- **Skizze:** FontAwesome → Inline-SVGs; confetti/sortablejs nur seitenweise statt global; Bootstrap/jQuery-Notwendigkeit auf der Money-Home prüfen; kritisches CSS inlinen, Rest self-hosted + `defer`. Vorher/nachher `pagespeed.web.dev`.
- **Akzeptanz:** Mobile-LCP messbar gesenkt; CWV „gut" auf `/`.

**A4 · Brand-Subtag deutscher** — ICE **5.7** · S · *nach A2*
- Subtag „JLPT N5 · auf Deutsch" → „Japanisch lernen · auf Deutsch · aus der Schweiz" (`base.html:120-123`). Markenname **nicht** ändern (SEO-Equity).

**A5 · Globale Events + SW früher registrieren** — ICE ~6.5 · S · *Teil von A1 / koordiniert mit G3*
- `streak_milestone`, `kana_game_played` an bestehende Handler hängen; Service-Worker-Registrierung von „ab Streak ≥3" (`base.html:55`) auf „nach 1. Session" vorziehen (Vorbereitung Push G3).

---

### Stream B — Pre-Login-Angebot & Bundle-Page (`lesson_paywall.html`, `n5_bundle.html`, `bundle_service.py`)

**B1 · Gast sieht Preis/Garantie/Payment (FLAGSHIP)** — ICE **8.7** · S
- **Problem:** Reassure-Block (TWINT/Visa/Mastercard/Apple-Google-Pay über Payrexx + „30 Tage Geld zurück · Schweizer Anbieter") liegt nur im `{% if current_user.is_authenticated %}`-Zweig (`n5_bundle.html:274-309`). Auf der **Paywall** sieht ein Gast **gar keinen Preis** — nur „brauchst ein kostenloses Konto" (`lesson_paywall.html:210-216`); Preisvergleich/Garantie/Trust-Row stecken im `else`-Zweig (`:270-278`).
- **Impact:** Free→Paid + Registrierungs-Start-Rate (Wert wird im stärksten Kaufimpuls verschwiegen).
- **Skizze:** Preisvergleich (Bundle 9.90 vs Single 5, durchgestrichen 14.90) + Garantie + Payment-Logos **auch für Gäste** rendern; CTA → „Kostenlos registrieren & freischalten →" mit `next=request.path`. Wert zuerst, Login zuletzt.
- **Akzeptanz:** Gast (ausgeloggt) sieht auf `/lessons/<paid>` und `/n5-bundle` Preis + Garantie + Logos über dem Fold.

**B2 · Early-Bird als echter Preis-Trigger** — ICE **6.7** · S
- Coverage-Balken (`n5_bundle.html:340-364`) mit Preis verknüpfen: „Bei 80 % Coverage steigt der Preis auf CHF 14.90 — aktuell 38.5 %." Macht Status zum Now-Hebel.

**B3 · Anti-Abo-Frame + Klubschule-Anker** — ICE **8.0** · S
- **Problem/Chance:** Ganzer Wettbewerb Abo + englisch; CHF 9.90 einmalig unterbietet selbst Lifetime-Optionen. Lokaler Anker: Klubschule Migros ZH CHF 741 für **einen** A1-Teilkurs.
- **Skizze:** „CHF 9.90 — einmal zahlen, kein Abo, für immer" + Mini-Jahrespreis-Vergleich (CHF) + Anker-Block „Ein Klubschul-Kurs kostet CHF 741. Bei uns CHF 9.90 — lerne wann du willst." Faktisch, mit Quelle; keine abwertenden Marken-Claims.
- **Akzeptanz:** Anti-Abo + Anker above-the-fold auf Bundle (Home-Variante → E1).

**B4 · Zahlen-Konsistenz + „Komplett"-Framing + Frische-Signal** — ICE **7.7** · S
- **Problem:** Home „510 Vok/55 Kanji", Bundle „Ziel 710/80, real 273/44", Über „31 Lektionen" vs „36". „N5 Komplett" + sichtbar 38.5 % = Erwartungslücke.
- **Skizze:** Eine projektweite „heute X von Ziel Y"-Sprache (Single Source = `bundle_service`/Coverage). Framing „der vollständige N5-Pfad, heute zu X % gefüllt, Rest inklusive". „Zuletzt aktualisiert vor N Tagen / +N Lektionen in 7 Tagen" als ehrliches Aktivitätssignal (gegen „verlassenes Solo-Projekt"-Angst). *(Home-Seite: siehe E4.)*

**B5 · „Doppelte Garantie"-Wording entwirren** — ICE **6.7** · S
- „Doppelt" (30-Tage + 6-Monats-Stagnation) verwirrt. Titel „Geld-zurück-Garantie — gleich zweifach abgesichert", 30-Tage-Zeile optisch dominant; „ohne Begründung, eine Mail genügt" führt (`n5_bundle.html:371-377`, `ueber.html:133` → mit F1 abgleichen).

**B6 · Bundle-Eyebrow entschärfen** — ICE **7.0** · S
- „Schweizer Solo-Projekt" direkt über dem Preis triggert Bestand-Zweifel → auf „in der Schweiz gemacht" (Home-Konsistenz); „Solo-Projekt"-Ehrlichkeit per `/ueber`-Link statt über dem Preis.

**B7 · Founder-Mini-Badge** — ICE ~7.0 · S · *Asset aus F2*
- „Gebaut von Claudio aus Rorschach — ich antworte selbst" als kompaktes Badge auf Bundle + Paywall (Trust-Anker am Kaufpunkt).

**B8 · Preis-Anker nach oben (strategisch)** — ICE **5.7** (I=8) · M
- **Chance:** Nur 9.90/14.90/5.00 (`bundle_service.py`) — kein Anker darüber; „komplettes N5 lifetime" für ~10 CHF signalisiert „zu billig". Benchmarks WaniKani $299, Bunpro $150.
- **Skizze:** Sichtbare höhere Stufe als Anker, z. B. „N5 + N4 Komplett" (CHF 39–49). **Tutoring-Tier vermeiden** (kollidiert mit Solo-Positionierung). 9.90 wird sichtbares Schnäppchen, ARPU-Lift bei den Zahlungsbereitesten.
- **Dateien:** `bundle_service.py`, `n5_bundle.html`, neuer Course.

---

### Stream C — Lessons-Liste & Einzel-Checkout (`lessons.html`, `purchase.html`)

**C1 · Bundle-Banner auf `/lessons`** — ICE **7.3** · S
- Bundle erscheint dort nur als Topnav-Tooltip; jede Paid-Lektion zeigt isoliert „5.00 CHF". Persistenter Banner: „Alle Premium-Lektionen lifetime für CHF 9.90 — günstiger als 2 Einzelkäufe." (`lessons.html` nach Hero, Daten aus `bundle_service`).

**C2 · Single-Checkout ins Sumi-System + Bundle-Upsell** — ICE **7.0** · S/M
- `purchase.html` ist eine Bootstrap-Insel (`:10-40`, `bg-primary`/`btn-success`/Modal) im Tailwind/Sumi-System → Vertrauensbruch im Kaufmoment; Bundle wird hier **nicht** mehr gezeigt. Ins Designsystem überführen (oder Single inline auf Paywall) + dezenter „Lieber alles? Bundle CHF 9.90 (nur CHF 4.90 mehr)"-Hinweis.

**C3 · Gratis-Stufen-Analyse** — ICE **5.3** · S (Analyse) / M (Umsetzung)
- ~39 % der Lektionen gratis (14/36). Risiko: ganze Kern-Module (z. B. komplettes Hiragana/Katakana) gratis → fehlender Kaufanreiz. **DB-Check via `/cloud-db`**; Faustregel: 1 Gratis-Teaser **pro Modul**, nicht ganze Module. Kein Code-, sondern Daten-/Content-Entscheid.

---

### Stream D — Auth & Lektions-Aktivierung (`routes.py` auth/index/view_lesson, `register.html`, `forms.py`, `lesson_view.html`, `module_detail.html`)

**D1 · `register()` `next`-Fix + Auto-Login (FLAGSHIP-Bug)** — ICE **8.7** · S
- **Problem (verifiziert):** `routes.py:439-450` liest `next` nicht, ruft kein `login_user()`, leitet auf `/login` („Sie können sich jetzt anmelden"). Paywall/Bundle übergeben `register(next=...)` → verpufft; `register.html` hat kein hidden `next`. `login()` macht `next` korrekt (`:470-478`) → Inkonsistenz an der teuersten Stelle.
- **Skizze:** Nach `commit()` direkt `login_user(user)`; Redirect auf validiertes `next` (Open-Redirect-Schutz aus `login()` wiederverwenden); hidden `next`-Field in `register.html`; Fallback → erste Lektion/`#lernpfad` mit Willkommens-Flash.
- **Akzeptanz:** Registrierung von einer Paywall führt eingeloggt zurück auf die Kaufseite, ohne 2. Login. `sign_up`-Event feuert.

**D2 · Register-Formular entschlacken** — ICE **6.3** · S
- 4 Pflichtfelder (Username+E-Mail+PW+PW2) + harte Passwortregel nur server-seitig nach Submit (`forms.py:16-24`, `register.html:33-35`). Username = reine Friktion. → Username optional/aus E-Mail ableiten; Passwort-Anforderungen sichtbar + Live-Check; `password2` weg + Show/Hide; Google-OAuth als ersten Pfad lassen.

**D3 · Gast-Celebration + „Fortschritt sichern"-CTA** — ICE **7.7** · M
- **Problem:** Confetti + „おめでとう!"-Modal feuern nur bei Server-Progress 100 % via `@login_required` (`lesson_view.html:2219-2221`); Gäste bekommen **nie** Erfolgserlebnis/Fortschritt (`routes.py:1129` legt keinen Gast-Progress an).
- **Skizze:** Clientseitige Gast-Celebration beim letzten Item (Confetti + Gast-Modal) mit Primär-CTA „Fortschritt sichern → Konto erstellen" (→ D1-Flow). `lesson_complete`/`lesson_start`-Events.
- **Akzeptanz:** Ausgeloggter Gast erreicht am Ende einer Gratis-Lektion eine Feier + Konto-CTA.

**D4 · Modul-CTA-Sackgasse beheben** — ICE **6.3** · S/M · *Mini-Abstimmung mit E (index.html)*
- Im „Kanji-Grundlagen"-Modul ist die **erste** Lektion gesperrt (price 5, kein Gast-Zugang); gratis erst ab Position 6 → „Beginnen →" landet auf Paywall, widerspricht „keine Sperren". CTA-Ziel auf erste gratis+guest-Lektion des Moduls (`routes.py:359-381` `first_free_guest_lesson` berechnen; `index.html:217-233`/`module_detail.html` nutzen).

**D5 · Lesson-Interlinking + Course-JSON-LD-Fix** — ICE **6.3** · M
- `/lessons/<id>` hat dünne interne Verlinkung und **kein** Course-JSON-LD (Grep `"@type":"Course"` → 0, obwohl behauptet). → „Nächste/vorherige Lektion im Modul" + „Alle N5-Module" + Bundle-CTA in jede Lektion; Course-Schema rendern/reparieren (Rich-Results-Test). `lesson_view.html` (+ ggf. `view_lesson`).

**D6 · Feedback-Sammelmechanik** — ICE **6.3** · M
- Kein Mechanismus für zitierbare Stimmen (ehrlich testimonial-los). → Nach Lektion-Abschluss/Streak-Meilenstein dezenter „1 Satz Feedback?"-Prompt mit Opt-in „darf zitiert werden (Vorname/Kanton)". Neues `UserFeedback`-Model/Route + Hook im Abschluss-State (`lesson_view.html`). Speist später echten Social Proof (statt Fake-Testimonials Übergangs-Platzhalter „Noch jung — dein Feedback formt die Plattform").

---

### Stream E — Home/Landing-Messaging & Aktivierung (`index.html`)

**E1 · Differenzierung above-the-fold** — ICE **7.7** · M
- **Problem:** „Warum besser?" wird im Hero nicht beantwortet; Differenzierung liegt vergraben auf `/jlpt-n5-schweiz` + `/ueber`. Duolingos dokumentierte JP-Schwächen (kein strukturiertes Grammatik-Verständnis, Lückentext-Raten, stoppt bei Kanji) = exakt eure Stärke.
- **Skizze:** „Für wen/statt was"-Zeile unter Subhead **ohne** Markennamen: „Für Erwachsene, die das *Warum* hinter jedem Satz verstehen wollen — strukturierte Grammatik auf Deutsch." Optional 3-Icon-Streifen „Auf Deutsch erklärt · Kein Abo, Lifetime · FSRS". (Format-Argument gg. Renshuu/WaniKani: „Kein überladenes Dashboard — ein klarer N5-Pfad.")
- **Akzeptanz:** Nutzenversprechen + Differenzierung in 5 Sek. sichtbar; `vowel_demo_played`/Bounce messbar.

**E2 · „Kostenlos starten" → erste Gast-Lektion** — ICE **8.0** · M
- CTA → `/lessons?access=free` = Liste (`index.html:55`). Gast-Access existiert (live: `/lessons/171-175`, `160` rendern ohne Login). → Deep-Link auf erste guest-zugängliche Hiragana-Lektion (Lesson 146, `price 0` + `allow_guest_access`); Liste bleibt sekundär.

**E3 · Vokal-Probe → CTA bei 5/5** — ICE **8.3** · S
- Bei 5/5 ändert sich nur Hero-Subtext (`index.html:1148-1152`) — kein Button. → Animierten Inline-CTA „→ Erste Lektion starten" (Deep-Link Lesson 146) einblenden; `vowel_demo_played`-Event (Hook für A1/competitive F5: `data-demo="vowel"`).

**E4 · Home-Zahlen-Konsistenz** — ICE **7.7** · S
- Home-Subhead an die „heute/Ziel"-Sprache (B4) angleichen, z. B. „Schon 273 von 710 N5-Vokabeln + 44 Kanji — wöchentlich mehr, auf Deutsch erklärt." `ueber.html:142` Lektionszahl von hartcodiert auf DB-Variable. *(Abstimmen mit B4 — gleiche Quelle.)*

**E5 · Headline-A/B-Test** — ICE **5.7** · S · *braucht A1*
- H1 „Hiragana am Morgen. Kanji am Abend." ist Vibe, kein Value-Prop. Gegen Varianten testen (Var. C zuerst, risikoärmste): H1 bleibt, Sub schärfen → „Der ganze JLPT-N5-Weg auf Deutsch — strukturiert statt Raten. Gratis starten, ohne Abo." (Var. A nutzen-/zielgruppen-explizit, Var. B Duolingo-Konter ohne Namen — siehe Anhang.)

**E6 · „Dein Start"-Strip + Mobile-Probe** — ICE ~5.7 · S
- Eingeloggter Neuling (0 Progress): 3-Punkte-„Dein Start"-Strip im Hero. Mobile: Vokal-Probe näher an den Hero-CTA / Mini-Teaser über dem Fold (`index.html:87-104` rutscht mobil unter den Fold).

---

### Stream F — Trust, Legal & Content-Korrektheit (`ueber.html`, `agb.html`, `jlpt_n5_schweiz.html`, DB-Content)

**F1 · AGB an Garantie angleichen (Pflicht)** — ICE **8.3** · S
- **Problem:** AGB §5 (`agb.html:36-41`) „Widerrufsrecht erlischt mit Beginn der Bereitstellung", Refund nur bei techn. Mängeln — widerspricht beworbener „30-Tage-Rückerstattung ohne Begründung" (`n5_bundle.html:373`, `ueber.html:133`, `lesson_paywall.html:271`). Glaubwürdigkeits- **und** Rechtsrisiko.
- **Skizze:** AGB §5b verbindliche Klausel „Freiwillige 30-Tage-Zufriedenheitsgarantie: voller Refund auf formlose Mail, ohne Begründung" (mit `widerruf.html:13-22` abgleichen). → Werbung = AGB.

**F2 · Founder-Gesicht auf `/ueber`** — ICE **7.7** · S/M
- Starke ehrliche Story, aber reiner Text (kein Foto/Signatur). → Foto + handschriftliche Signatur (`ueber.html:18-19`); Asset speist Mini-Badge B7. Stärkster authentischer Trust-Anker bei Solo-Anbieter.

**F3 · „ß" → „ss" auf `/ueber`** — ICE **8.3** · S
- 3× sichtbares ß auf indexierter Seite: „großen" (`:24`), „Großartiges" (`:43`), „Außerdem" (`:97`). → grossen/Grossartiges/Ausserdem. Zahlt direkt aufs „Swiss-made"-Versprechen ein. *(Nicht-sichtbare ß in CSS-Kommentaren/`review.html` = niedrige Prio.)*

**F4 · JLPT-Datum-Faktencheck** — ICE **7.3** · S
- `/jlpt-n5-schweiz` nennt fix „6. Dez 2026 UZH (CHF 130)". UZH-Quelle: Anmeldung 2026 „erst Sommer offen", 2025 in CH **nicht** durchgeführt. → Datum weichzeichnen („typischerweise Juli/Dez, Anmeldung Sommer 2026 — aktueller Stand: UZH") + Outbound-Quelllink `aoi.uzh.ch` (E-E-A-T). Meta in `routes.py:825-833` mitziehen.

**F5 · Mayuko-Anonymisierung im DB-Content (Compliance)** — ICE ~6.7 · S · **Pflicht (Regelverstoss)**
- **DB-verifiziert:** „Mayuko" öffentlich in **16 `lesson_content`-Items / 9 publizierten N5-Lektionen** (IDs 149,158,163,165,169,171,172,173,175; z. B. „Lerntipp von Mayuko"). Verstoss gegen „Mayuko nie öffentlich".
- **Skizze:** Content-Migration → „Tipp von deiner Lehrerin" o. ä. Reines Content-Edit (`lesson_content.content_text`), kein Template. **Mit DB-Backup**, separat von Code-Streams.

---

### Stream G — Retention/Lifecycle-Aussenkanal (`mail_service.py`, `models.py`, `sw.js`, `srs_routes.py`, `requirements.txt`, neue Cron, `templates/email/`)

> Kerneinsicht: On-Site-Retention ist stark — es fehlt der **Aussenkanal**, um abgesprungene Nutzer zurückzuholen.

**G1 · E-Mail-Lifecycle (FLAGSHIP-Retention)** — ICE **7.7** · M
- **Problem:** Einziger Mail-Versand = `send_password_reset_email`. Flask-Mail ist aber voll konfiguriert (Hostpoint SMTP, `__init__.py:134-180`) → Infra brach. Kein Opt-in/Consent-Feld im User-Model (DSGVO-Pflicht).
- **Skizze:** (a) `email_reminders`-Opt-in + Registration-Checkbox; (b) Daily-Due-Reminder via Cron/systemd-Timer (Backup-Timer als Muster); (c) Win-back-Sequenz 7/14/30 Tage. Templates analog `reset_password.{html,txt}`.
- **Impact:** D7/D30 + Reaktivierung (EdTech 10–35 % Re-Engagement; 4-Mail-Sequenz +137 % vs Einzel).
- **Akzeptanz:** Opt-in-User mit fälligen Karten erhält eine Reminder-Mail, die auf `/review` deeplinkt.

**G2 · Streak-UTC-Bugfix + Milestones** — ICE **6.7** · S (Fix) / M (Milestones)
- **Bug (verifiziert):** `update_streak` nutzt `datetime.utcnow().date()` (`models.py:65`); CH = UTC+1/+2 → späte Abend-Sessions fallen auf den UTC-Vortag → Streak kann fälschlich brechen. → auf `Europe/Zurich` umstellen + verifizieren. Plus: Streak-Milestones mit Reward (7/30 Tage → Bonus-XP/Badge); Abend-Reminder nur an aktive-Streak-aber-heute-inaktiv-User.

**G3 · Web-Push aktivieren (toter Code)** — ICE **6.3** · M
- SW (`sw.js`) hat fertigen Push-Handler, `/api/user/push-subscribe` (`srs_routes.py:592`) speichert Abos — aber `requestPermission()`/`pushManager.subscribe()` kommen **nirgends** vor, `pywebpush`/VAPID fehlt in `requirements.txt`. → `pywebpush` + VAPID-Keys (.env); sanftes In-App-Permission-Prompt nach 1. Session; Versand im selben Cron wie G1; SW früher registrieren (A5). *(iOS-Safari-Push eingeschränkt.)*

**G4 · Wochen-Digest-Mail + „0 %"-Anzeige verifizieren** — ICE **6.0** · S
- Stats-Seite ist ein starkes Asset (Heatmap, Forecast, Maturity, Achievements). → Wochen-Digest („Deine Woche: X Reviews, Y % Erfolg, Heatmap-Preview"; personalisierte Betreffe 31 % vs 18 % Open-Rate). **Vorher** „Erfolgsrate 0 %"-Anzeige trotz 58 Karten prüfen (`srs_service.get_user_stats`) — sonst demotivierende Mail.

**G5 · Daily-Challenge als Habit-Hook** — ICE **6.3** · S/M
- Daily-Challenge existiert (`srs_routes.py:809-859`, 25 Bonus-XP), aber nicht prominent als täglicher Anker und nicht mit Streak/Reminder gekoppelt. → „Heutige Challenge ✓/offen" auf Home/Nav; in Due-Reminder/Push verlinken; Abschluss als Streak-Aktivität.

**G6 · Achievement-Aussen-Benachrichtigung** — ICE **5.7** · S · *braucht G1/G3*
- `UserAchievement.notified`-Flag existiert; Unlocks werden nur in-session gefeiert. → `notified=False`-Achievements in Digest/Push als niederschwelliger Win-back-Anlass.

**G7 · SRS/Kana Empty-State-Guidance** — ICE **5.7** · M
- `/review` + `/practice/kana` sind `@login_required` und für Tag-1-User leer (SRS zählt nur Kana aus abgeschlossenen Lektionen). → Empty-State mit „Schliesse zuerst Hiragana 1 ab" (Deep-Link 146); optional Kana-Spiel als read-only Gast-Demo. Macht den Kern-Differenzierer SRS für Neulinge sichtbar.

**G8 · Premium/Abo-Churn-Lifecycle** — ICE **5.3** · M · *abhängig von Payrexx-Live (aktuell Mock)*
- `PaymentService.check_expired` ist nur ein Kommentar, kein Job. → periodischen Job aktivieren; „Abo endet in 3 Tagen"- + Post-Cancel-Win-back-Mail (auf G1-Infra). Sichert LTV bei Go-Live.

---

### Stream H — SEO / Organic Acquisition (`seo_routes.py`, neues `content_routes.py` + Templates, `routes.py` learn_path)

**H1 · `/learn/n5` 301-Fragment → echte N5-Hub-Seite** — ICE **7.7** · S/M
- **Problem:** `curl -sI /learn/n5` → 301 auf `/#lernpfad` (`routes.py:847`). Fragmente ignoriert Google → generischste N5-URL sammelt keine eigene Ranking-Autorität.
- **Skizze:** `/learn/n5` als eigene 200-Seite (Module + Lernpfad + Bundle-CTA), Self-Canonical; Home-`#lernpfad` nur Teaser, der dorthin verlinkt. Genau der Ranking-Hebel bei Pos. ~31.

**H2 · Programmatic-SEO-Hub + Ratgeber-Blog (GROSSE WETTE)** — ICE **6.7** (I=9) · L
- **Chance:** `/kanji/父`, `/kana`, `/hiragana/a`, `/wortschatz` → alle 404; kein Blog. DB: 200 Kana + 61 Kanji + 519 Vokabeln + 127 Grammatik = ~900 mögliche Long-Tail-Seiten, alle hinter Lesson-Seiten eingesperrt. Info-Intents auf Deutsch nur von `.de` besetzt — **kein CH-Player**.
- **Skizze:** (a) SSR-Einzelseiten `/hiragana/<kana>`, `/kanji/<char>`, `/wortschatz/<id>` (eigener Title/Meta/H1, JSON-LD, „Im Kurs lernen"-CTA); (b) `/ratgeber/`-Guides („Hiragana in 2 Wochen", „JLPT N5 Wortschatzliste", „Japanisch lernen als Schweizer:in"); alle in Sitemap. **Schrittweise, Kana zuerst.** Eigenes `content_routes.py`-Blueprint (kein `routes.py`-Konflikt). Grösster mittelfristiger Traffic-Treiber + speist interne Verlinkung auf Money-Pages.
- **Achtung Soft-404:** SSR Pflicht (keine JS-only-/`/api`-Listen — `/api` ist robots-blockiert).

**H3 · robots.txt / AI-Bots (Strategie-Entscheid)** — ICE **6.3** · S
- Cloudflare-Managed robots.txt sperrt ClaudeBot/GPTBot/Google-Extended (`Disallow: /`). Klassische Suche offen (gut), aber AI-Answer-Engines dürfen nicht zitieren. → mind. **Google-Extended** (= AI Overviews) freigeben erwägen; `ai-train=no` darf bleiben. **Im Cloudflare-Dashboard**, nicht im Repo.

**H4 · Modul-Slugs vereinfachen** — ICE **5.3** · M · *nach H1/H2*
- `/learn/n5/n5-hiragana` dupliziert die n5-Ebene und drängt das Keyword nach hinten. → `/learn/n5/hiragana` etc. **mit 301** von alten Slugs (`LessonCategory.slug`-Migration, `routes.py:852`, Sitemap). Niedrige Prio.

---

## Anhang

### A. Headline-Varianten (E5, gegen Original A/B-testen)
- **Var. A (Nutzen+Zielgruppe):** H1 „Japanisch bis JLPT N5 — auf Deutsch erklärt." / Sub „Hiragana, Kanji und Grammatik strukturiert, mit Spaced Repetition. Für Anfänger ohne Vorwissen. Gratis starten."
- **Var. B (Konter ohne Namen):** H1 „Endlich verstehen *warum* — nicht nur Lücken füllen." / Sub „JLPT-N5-Japanisch auf Deutsch erklärt. Aus der Schweiz, kein Abo, Lifetime."
- **Var. C (risikoärmste — zuerst):** H1 bleibt „Hiragana am Morgen. Kanji am Abend." / Sub „Der ganze JLPT-N5-Weg auf Deutsch — strukturiert statt Raten. Gratis starten, ohne Abo."

### B. Wettbewerbs-Benchmarks (competitive)
Duolingo Super ~$95.99/J · WaniKani $89/J ($299 Lifetime, Sale ~$199) · Bunpro $50/J ($150 Lifetime) · Renshuu $49.99/J ($109.99 Lifetime) · Busuu ~$63/J · Klubschule Migros ZH **CHF 741 / A1-Teilkurs**. Lücke: **kein deutschsprachiger, struktur-geführter N5-Self-Study-Anbieter mit SRS + Lifetime-statt-Abo.**

### C. Finding-Herkunft (Disziplin → Tasks)
- **Positioning:** F1→B4/E4 · F2→E1 · F3→F3 · F4→A4 · F5→E5 · F6→B6
- **CRO:** F1→D1 · F2→E2 · F3→A2 · F4→C2 · F5→D2 · F6→E6
- **Pricing:** 1→B1 · 2→C1 · 3→C2 · 4→B2 · 5→B8 · 6→B4 · 7→C3 · 8→(Backlog: Geschenk-Gutschein/Lizenzen, L)
- **SEO:** F1→H2 · F2→H1 · F3→A3 · F4→F4 · F5→H3 · F6→H4 · F7→D5
- **Trust:** T1→B1 · T2→F1 · T3→F2/B7 · T4→D6 · T5→B4 · T6→B5
- **Onboarding:** F1→D3 · F2→E3 · F3→D1 · F4→D4 · F5→G7 · F6→E6/Aktivierungs-Kette · Nebenbefund→F5
- **Retention:** F1→G1 · F2→(Empfangsseite ok) · F3→G2 · F4→G3 · F5→G4 · F6→G5 · F7→G6 · F8→G8
- **Competitive/Analytics:** F1→A1 · F2→B3/E1 · F3→B3 · F4→E1 · F5→E3-Event · F6→A1-Enabler

### D. Backlog (niedrigste Prio / spätere Wellen)
- Pricing #8: Geschenk-Gutschein („Japanisch verschenken") + Gruppen-/Schul-Lizenz (neuer Voucher-Service, L).
- Onboarding F6 (Golden-Path-Verkettung) ist ein **Dach-Hebel** über D1/D3/E2/E3 — entsteht grösstenteils, wenn diese Tasks umgesetzt sind; als explizites Activation-Event in Analytics (A1) verankern.

---

*Erstellt vom Marketing-Team (8 Disziplinen, Opus 4.8) · Synthese & Priorisierung: Lead · Stand 2026-05-31.*
