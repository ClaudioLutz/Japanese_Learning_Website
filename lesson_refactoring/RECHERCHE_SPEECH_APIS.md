# Recherche: Text-to-Speech APIs für Japanisch (Stand März 2026)

## Anforderungen für eine Japanisch-Lernplattform
- Sehr klare Aussprache (pädagogisch nutzbar)
- Einstellbare Geschwindigkeit (langsam für Anfänger)
- Phonem-Kontrolle (IPA/SSML) für exakte Aussprache
- Mehrere Stimmen (männlich/weiblich)
- API-Integration für automatische Generierung

---

## Vergleich

| Anbieter | JP-Qualität | Stimmen (JP) | Preis/1M Zeichen | SSML/Phoneme | Speed-Kontrolle | Eignung |
|---|---|---|---|---|---|---|
| **Google Cloud TTS** | Sehr gut | ~12+ | $4-24 | Ja (IPA) | Ja | ★★★★★ |
| **Microsoft Azure TTS** | Sehr gut | ~9 | $15-16 | Ja (IPA) | Ja | ★★★★★ |
| **VOICEVOX** (Open Source) | Gut | 40+ | Gratis | Mora-Kontrolle | Ja | ★★★★★ |
| **Fish Audio S2** | Sehr gut | Community | $15/M Bytes | Wort-Level | Ja | ★★★★ |
| **Qwen3-TTS** (Open Source) | Gut-Sehr gut | Flexibel | Gratis | Emotion | Ja | ★★★★ |
| **CoeFont** | Sehr gut | 10'000+ | Auf Anfrage | Limitiert | Ja | ★★★★ |
| **VOICEPEAK** | Hervorragend | Mehrere | Einmalkauf ~130 CHF | Emotion | Ja | ★★★★ |
| **Amazon Polly** | Gut | 4 (2 Neural) | $4-16 | Ja | Ja | ★★★ |
| **ElevenLabs** | Mittelmässig (JP) | 150+ | $240-300 | Nein | Limitiert | ★★ |
| **OpenAI TTS** | Schlecht (JP) | 13 | $15-30 | Nein | Nein | ★ |
| **Kokoro TTS** | Schlecht (JP) | Wenige | Gratis | Nein | Limitiert | ★ |

---

## Detailanalyse der Top-Kandidaten

### 1. Google Cloud TTS — Beste Cloud-Lösung

**Stimmen:** 12+ japanische Stimmen (Standard, WaveNet, Neural2, Chirp 3 HD)
- 4 weiblich, 4 männlich als Kern
- Chirp 3 HD: Neueste Generation, 8 Sprecher

**Preis:**
- Standard: $4/1M Zeichen
- WaveNet/Neural2: $16/1M Zeichen
- Chirp HD: $24/1M Zeichen
- **Gratis:** 1M WaveNet + 4M Standard-Zeichen/Monat

**Warum ideal für Sprachlernen:**
- SSML mit `<phoneme alphabet="ipa">` — exakte Aussprachekontrolle
- `<prosody rate="slow">` — stufenlose Geschwindigkeit
- `<break time="500ms"/>` — Pausen zwischen Wörtern
- Latenz: 150-300ms

**Kostenrechnung für 12 Lektionen:**
- ~50 Vokabeln × 12 Lektionen × ~20 Zeichen = ~12'000 Zeichen
- ~30 Beispielsätze × 12 × ~40 Zeichen = ~14'400 Zeichen
- ~7 Dialogzeilen × 12 × ~30 Zeichen = ~2'520 Zeichen
- **Total: ~29'000 Zeichen → innerhalb des Gratis-Kontingents!**

---

### 2. Microsoft Azure TTS — Beste Stimmvielfalt

**Stimmen:** ~9 japanische Stimmen
- Nanami (weiblich): Mehrere Stile — Chat, Customer Service, Cheerful
- Keita, Daichi, Naoki, Masaru (männlich)
- Aoi, Mayu, Shiori (weiblich)

**Preis:**
- Neural: $15-16/1M Zeichen
- **Gratis:** 5M Zeichen/Monat (!)

**Warum interessant:**
- Emotionale Stile pro Stimme (cheerful, sad, angry)
- Word Boundary Events — Wort-für-Wort-Hervorhebung möglich
- Visemes für Lippensynchronisation
- Grösstes Gratis-Kontingent

---

### 3. VOICEVOX — Beste japanisch-spezialisierte Lösung

**Stimmen:** 40+ Charaktere, ausschliesslich Japanisch

**Preis:** Komplett kostenlos (Open Source)

**Warum einzigartig:**
- **Mora-Level-Intonationskontrolle** — jede Mora (Silbe) einzeln anpassbar
- Speziell für japanische Prosodie entwickelt
- REST-API (FastAPI-basiert, localhost)
- Läuft komplett offline
- Einstellbare Geschwindigkeit und Tonhöhe pro Charakter

**Einschränkung:**
- Self-Hosting erforderlich (Docker oder lokale Installation)
- Lizenzbedingungen pro Charakter beachten (kommerziell meist erlaubt)

---

### 4. VOICEPEAK — Höchste Qualität (Offline)

**Stimmen:** Mehrere hochwertige japanische Stimmen mit Emotionskontrolle

**Preis:** Einmalkauf ~130 CHF

**Warum erwähnenswert:**
- "State-of-the-art" japanische Sprachsynthese (Syllaflow-Engine)
- Emotionssteuerung (Freude, Trauer, Wut)
- Ideal für Vorproduktion von Audio-Dateien

**Einschränkung:**
- Kein Cloud-API — nur Desktop-Software
- Geeignet für Batch-Produktion, nicht für Echtzeit

---

## Empfehlung: Hybrid-Ansatz

### Primäre Lösung: Google Cloud TTS

**→ Google Cloud TTS (WaveNet oder Neural2)**
- Audio in der Generierungs-Pipeline erzeugen und als MP3 speichern
- SSML-Kontrolle für pädagogische Anpassung:
  - `<prosody rate="slow">` für Anfänger-Geschwindigkeit
  - `<phoneme alphabet="ipa">` für exakte Aussprache
  - `<break time="500ms"/>` für Pausen zwischen Wörtern
- Bereits im GCP-Ökosystem (Cloud Run, Cloud SQL)
- Gratis-Kontingent: 1M WaveNet-Zeichen/Monat → reicht für alle Lektionen

### Kostenvergleich für 12 Premium-Lektionen

| Ansatz | Kosten |
|---|---|
| **Google Cloud WaveNet (Free Tier)** | **$0** |
| Google Cloud WaveNet (über Free Tier) | ~$0.50 |
| Azure TTS (Free Tier) | $0 |
| ElevenLabs | $7-9 |
| OpenAI TTS | ~$0.50 (aber schlechte JP-Qualität) |

---

## Entscheidung

- [x] **Google Cloud TTS (WaveNet/Neural2)** — Primäre Lösung
  - Bereits im GCP-Ökosystem (Cloud Run, Cloud SQL)
  - SSML mit IPA-Phonem-Kontrolle + Geschwindigkeitsanpassung
  - Gratis-Tier: 1M WaveNet + 4M Standard-Zeichen/Monat → reicht für unser Volumen
  - 12+ japanische Stimmen (männlich/weiblich)
  - Kosten für 12 Lektionen: **$0** (innerhalb Gratis-Kontingent)
- [x] ~~VOICEVOX~~ — Ausgeschlossen (erfordert lokale GPU-Leistung, Laptop zu schwach)
- [ ] Azure TTS als Alternative evaluieren falls Google-Qualität nicht genügt

---

## Quellen

- [TTS APIs for Language Apps 2026 (DEV Community)](https://dev.to/pocket_linguist/text-to-speech-in-2026-comparing-5-tts-apis-for-language-apps-606)
- [Best TTS APIs (Fish Audio)](https://fish.audio/blog/top-tts-apis-developer-comparison-2026/)
- [Google Cloud TTS Pricing](https://cloud.google.com/text-to-speech/pricing)
- [Google Cloud Supported Voices](https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types)
- [Azure TTS Pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
- [Azure Japanese Voices](https://json2video.com/ai-voices/azure/languages/japanese/)
- [Amazon Polly Voices](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html)
- [ElevenLabs Japanese TTS](https://elevenlabs.io/text-to-speech/japanese)
- [OpenAI TTS Docs](https://developers.openai.com/api/docs/guides/text-to-speech)
- [VOICEVOX](https://voicevox.hiroshiba.jp/)
- [VOICEVOX Engine (GitHub)](https://github.com/VOICEVOX/voicevox_engine)
- [Fish Audio S2](https://fish.audio/s2/)
- [Qwen3-TTS (GitHub)](https://github.com/QwenLM/Qwen3-TTS)
- [Best TTS for Language Learning (Inworld)](https://inworld.ai/resources/best-voice-ai-for-language-learning-apps)
