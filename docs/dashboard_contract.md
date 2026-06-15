# „Mein Lernen" — eingefrorener Daten-Vertrag

Verbindliche Schnittstelle zwischen Frontend (Alpine-Komponente `dashboard()`) und
Backend. **Solange dieser Vertrag stabil bleibt, arbeiten FE- und BE-Tracks
unabhängig.** FE entwickelt gegen `app/static/dev/dashboard_mock.json` (identische
Form), BE liefert dieselbe Form aus echten Daten.

Aufteilung nach dem `/review/stats`-Muster:
- **A) Server-Render-Context** — in `dashboard_routes.index()`, sofort sichtbar (kein Fetch).
- **B) Lazy-Endpoints** `/api/dashboard/*` — erst beim Aufklappen/Tab-Wechsel/Pillar-Expand.

---

## A) Server-Render-Context (`render_template('learner_dashboard.html', **ctx)`)

```jsonc
{
  "name": "claudiolutz",                 // current_user.username            [EXISTS]
  "streak": 7,                            // current_user.current_streak      [EXISTS]
  "longest_streak": 14,                   // current_user.longest_streak      [EXISTS]
  "due_count": 12,                        // srs_service.get_user_stats        [EXISTS]
  "freezes": 1,                           // UserSRSSettings.streak_freezes_available (0/1) [EXTEND]
  "week_goal": {"done": 5, "total": 7},  // aktive CH-Tage lfd. Woche          [NEW]
  "plan": [                               // adaptiver Plan-Builder             [NEW]
    {"title":"…(HTML)","desc":"…","why":"…","dur":"~6 Min","kind":"review|lesson|drill","href":"/review"}
  ],
  "plan_minutes": 12,
  "pillars": [                            // 5-Bucket-Reife je Skill            [EXTEND]
    {"key":"kana","name":"Kana","icon":"fa-spell-check","started":200,"total":200,
     "target_pct":95,"dist":[neu,lernen,jung,reif,gemeistert],"sowhat":"…","cta":"Drill"}
    // key ∈ {kana,kanji,vocab,grammar[,listen]}; dist = ints; Bucket-Reihenfolge FIX.
  ],
  "numbers": {"kanji":47,"vocab":210,"grammar":18,"kana":200},  // begonnen je Typ [EXTEND]
  "can_do": [{"t":"Mich vorstellen…","s":"done|prog|open"}]      // kuratiert (Claude) [NEW]
}
```

`dist`-Reihenfolge ist kanonisch `[Neu, Lernen, Jung, Reif, Gemeistert]` und kommt aus
`gamification_service.maturity_bucket(status, stage_idx)` (Single Source). Ring-/Gate-/
Zonen-Mathe bleibt **clientseitig** (siehe `_js_dashboard.html`: `masteryPct`, `computeReadiness`).

## B) Lazy-Endpoints

| Endpoint | FE-Feld | Form | Status |
|---|---|---|---|
| `GET /api/dashboard/compass-glyphs?type=kanji\|kana\|vocab\|grammar` | `kanji[]`/`kanaSample[]`/… | `[{"c","on","kun?","mean","acc":0-100,"reps"}]` | NEW (kana via `/api/srs/stats/kana-heatmap` EXISTS) |
| `GET /api/dashboard/confusion-pairs` | `confusionPairs[]` | `[{"id","a","b","aAcc","bAcc","note"}]` | NEW (`KanaConfusion` + kuratierte Notes) |
| `GET /api/dashboard/tempo` | `kpi`,`reviewsByWeek[8]`,`accuracyByWeek[8]`,`reviewsByWeekday[7]` | s. JS | NEW |
| `GET /api/dashboard/retention-maturity` | `retention{value,neu,jung,reif}` | ints | NEW |
| `GET /api/dashboard/acc-by-stage` | `accByStage[5]` | ints | NEW (Approx. v1) |
| `GET /api/srs/stats/heatmap` | `heatmap[365]` | `[{date,count}]` → counts | EXISTS |
| `GET /api/srs/stats/forecast?days=14` | Forecast-Basis | `[{date,count}]` | EXISTS |
| `GET /api/srs/stats/kana-heatmap` | `kanaRows` | s. `stats.html` filteredKanaRows | EXISTS |
| `GET /api/srs/stats/kana-weak?limit=5` | `weakKana[]` | reshape | EXISTS |
| `GET /api/srs/stats/leeches` | `leeches[]` | reshape (`front`,`content_type`→Label,`failure_rate`) | EXISTS |
| `GET /api/srs/stats/content-type` | `accBySkill[]` | reshape | EXISTS |
| `GET /api/srs/jlpt-progress` | JLPT Vokabeln/Kanji | EXISTS (+ Grammatik EXTEND) | EXISTS/EXTEND |
| `GET /api/srs/achievements` | `milestones[]` | + Rest-Text-Mapping | EXTEND |

Forecast-Kapazitäts-Hochrechnung (`scenarios`, `forecastNote`, `_fcData`) bleibt
**clientseitige Heuristik** — kein Backend-Bedarf.

## Regeln
- Endpoints **additiv** — bestehende `/api/srs/stats/*` NICHT in der Form ändern (`stats.html` nutzt sie weiter).
- Zahlen roh liefern; Tausender-Formatierung (`de-CH`, Apostroph) macht das FE (`toLocaleString('de-CH')`).
- Neue Aggregate **dialektneutral** (in Python aggregieren, nicht `date_trunc`) — Tests laufen auf SQLite.
