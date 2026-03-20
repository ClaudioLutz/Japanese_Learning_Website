# Recherche: Bild-Generierungs-APIs (Stand März 2026)

## Vergleich

| Modell | Preis/Bild (1024x1024) | Anime-Qualität | API | Bemerkung |
|---|---|---|---|---|
| **gpt-image-1 (High)** | $0.167 | Gut | OpenAI | Aktuell im Projekt, teuer |
| **gpt-image-1 (Medium)** | $0.04 | Gut | OpenAI | Guter Kompromiss |
| **gpt-image-1-mini** | $0.005-0.036 | Akzeptabel | OpenAI | Günstigste OpenAI-Option |
| **Flux 1.1 Pro** | $0.04 | Sehr gut | Black Forest Labs | Höchste Bewertung Artificial Analysis |
| **Flux 2 Pro** | $0.03-0.045 | Sehr gut | Black Forest Labs | Neuste Flux-Version |
| **Hunyuan Image 3.0** | $0.03 | Exzellent (Anime) | Tencent / Open Source | Spezialisiert auf asiatische Stile |
| **NovelAI V4.5** | $25/Mt. unlimitiert | Herausragend | NovelAI | Bester Anime-Stil, Abo-Modell |
| **Stability SD 3.5 Turbo** | $0.04 | Gut | Stability AI | Grosses LoRA-Ökosystem |
| **Google Imagen 4** | $0.02-0.06 | Solide | Vertex AI | Günstig, GCP nötig |
| **Ideogram v3** | $0.03-0.05 | Mittel | Ideogram | Stark bei Text-in-Bild |

## Kostenrechnung für ~1'000 Bilder

| Modell | Kosten |
|---|---|
| gpt-image-1 (High) — aktuell | **$167** |
| gpt-image-1-mini (High) | $36 |
| Flux 1.1 Pro | $40 |
| Hunyuan Image 3.0 | $30 |
| NovelAI Opus (1 Monat) | $25 |
| Google Imagen 4 (Fast) | $20 |

## Empfehlung

### Option A: Minimaler Code-Umbau
**gpt-image-1-mini** — Bleibt im OpenAI-Ökosystem, nur Modell-Name ändern.
Ersparnis: ~78% gegenüber aktuell.

### Option B: Beste Qualität/Preis
**Flux 1.1 Pro** — $0.04/Bild, sehr gute Anime-Qualität, einfache REST-API.
Erfordert neuen API-Client in `ai_services.py`.

### Option C: Bester Anime-Stil
**NovelAI V4.5 Opus** — $25/Monat unlimitiert, herausragender Anime/Manga-Stil.
Ideal für Batch-Generierung, aber Abo-Modell.

## Entscheidung
- [ ] Noch offen — Test-Vergleich mit 3 Bildern pro API nötig

## Quellen
- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Black Forest Labs Pricing](https://bfl.ai/pricing)
- [Best AI Image Generators 2026](https://wavespeed.ai/blog/posts/best-ai-image-generators-2026/)
- [NovelAI Pricing](https://aitoolsdevpro.com/ai-tools/novelai-guide/)
- [Hunyuan Image 3.0 Guide](https://wavespeed.ai/blog/posts/hunyuan-image-3-0-complete-guide-2026/)
