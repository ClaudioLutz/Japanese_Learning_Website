# tests/integration/test_kana_spell.py
"""Integration-Tests fuer das Kana-Schreibspiel (dritter Tab auf /practice/kana).

Deckt ab:
- /api/practice/kana/spell/words — der Wort-Pool. ENTSCHEIDEND: gefiltert auf
  `word` (Schriftform), NICHT `reading` -> Kanji-Woerter (Pfad C) bleiben draussen
  (Pfad A: reine Kana-Woerter). Plus Dakuten-Buendelung, Quelle alle|freigeschaltet,
  Laengen-/N5-Grenzen, Gast-offen, kein DB-Write.
- /api/practice/kana/spell-finish — Persistenz + grind-sichere XP (eigenes
  Tages-Budget, getrennt von Storm), Login-Pflicht, kein Aggregat-/FSRS-Eingriff.
- Der Schreiben-Tab + Deep-Link auf /practice/kana.
"""
from app.models import KanaSpellScore, DailyReviewAggregate, CardReviewState, User
from app.gamification_service import (
    XP_STORM_BASE, XP_STORM_RUN_BONUS_CAP, XP_STORM_DAILY_CAP,
)
from tests.factories import VocabularyFactory


def _vocab(db, word, reading=None, romaji='x', meaning_de='Bedeutung',
           jlpt_level=5, status='approved'):
    """Legt ein Vokabel an. jlpt_level=5 als INT (Prod-Format; die Factory
    defaultet auf den String 'N5', den der `== 5`-Filter nicht traefe)."""
    v = VocabularyFactory(word=word, reading=reading or word, romaji=romaji,
                          meaning_de=meaning_de, jlpt_level=jlpt_level, status=status)
    db.session.commit()
    return v


class TestSpellWordsEndpoint:
    """GET /api/practice/kana/spell/words — der freigeschaltete Wort-Pool."""

    def test_guest_can_load(self, client, db):
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        resp = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['guest'] is True
        assert data['source'] == 'all'

    def test_filters_on_word_not_reading(self, client, db):
        # DER Kernfall (Pfad A vs C): ein Kanji-Wort hat eine reine Kana-`reading`
        # (にほん), aber seine SCHRIFTFORM 日本 enthaelt Kanji -> NICHT schreibbar.
        # Ein Filter auf `reading` wuerde es faelschlich aufnehmen (Pfad C).
        _vocab(db, '日本', reading='にほん', romaji='nihon', meaning_de='Japan')
        _vocab(db, 'ねこ', reading='ねこ', romaji='neko', meaning_de='Katze')
        data = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all').get_json()
        words = {w['word'] for w in data['words']}
        assert 'ねこ' in words
        assert '日本' not in words

    def test_excludes_small_kana_and_sokuon(self, client, db):
        # Klein-Kana (ょ) + Sokuon (っ) stehen in keiner Reihen-Tabelle -> mit dem
        # word-Praedikat in EINEM Schritt raus (v1-Pool, keine Klein-Kana-Tiles).
        _vocab(db, 'がっこう', romaji='gakkou', meaning_de='Schule')   # っ
        _vocab(db, 'きょう', romaji='kyou', meaning_de='heute')       # ょ
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        data = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all').get_json()
        words = {w['word'] for w in data['words']}
        assert 'ねこ' in words
        assert 'がっこう' not in words
        assert 'きょう' not in words

    def test_dakuten_bundled_with_base_row(self, client, db):
        # rows=k: die Dakuten-Buendelung zieht die g-Reihe automatisch rein, damit
        # かぎ (か + ぎ) schon mit der K-Reihe schreibbar ist (keine Dakuten-Klippe).
        _vocab(db, 'かぎ', romaji='kagi', meaning_de='Schlüssel')
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')  # ね (n-Reihe) nicht im Scope
        data = client.get(
            '/api/practice/kana/spell/words?schrift=hiragana&source=unlocked&rows=k'
        ).get_json()
        words = {w['word'] for w in data['words']}
        assert 'かぎ' in words
        assert 'ねこ' not in words

    def test_unlocked_respects_rows(self, client, db):
        _vocab(db, 'あい', romaji='ai', meaning_de='Liebe')   # nur Vokale
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        data = client.get(
            '/api/practice/kana/spell/words?schrift=hiragana&source=unlocked&rows=vowels'
        ).get_json()
        words = {w['word'] for w in data['words']}
        assert 'あい' in words
        assert 'ねこ' not in words

    def test_all_mode_ignores_rows(self, client, db):
        # Default-Modus 'alle': die Reihen-Auswahl wirkt NICHT (nur Schrift zaehlt).
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        data = client.get(
            '/api/practice/kana/spell/words?schrift=hiragana&source=all&rows=vowels'
        ).get_json()
        words = {w['word'] for w in data['words']}
        assert 'ねこ' in words

    def test_length_bounds(self, client, db):
        _vocab(db, 'い', romaji='i', meaning_de='Magen')             # len 1 -> raus
        _vocab(db, 'あいうえおかき', romaji='x', meaning_de='zu lang')  # len 7 -> raus
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        data = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all').get_json()
        words = {w['word'] for w in data['words']}
        assert 'ねこ' in words
        assert 'い' not in words
        assert 'あいうえおかき' not in words

    def test_only_n5_approved(self, client, db):
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')                         # N5 approved
        _vocab(db, 'いぬ', romaji='inu', meaning_de='Hund', jlpt_level=4)             # N4 -> raus
        _vocab(db, 'うし', romaji='ushi', meaning_de='Kuh', status='pending_approval')  # pending -> raus
        data = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all').get_json()
        words = {w['word'] for w in data['words']}
        assert 'ねこ' in words
        assert 'いぬ' not in words
        assert 'うし' not in words

    def test_count_reflects_total(self, client, db):
        for w in ('ねこ', 'いぬ', 'うま'):
            _vocab(db, w, romaji='x', meaning_de='Tier')
        data = client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all').get_json()
        assert data['count'] == 3

    def test_empty_unlocked_yields_message(self, client, db):
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')  # braucht n+k
        data = client.get(
            '/api/practice/kana/spell/words?schrift=hiragana&source=unlocked&rows=vowels'
        ).get_json()
        assert data['count'] == 0
        assert 'message' in data

    def test_does_not_write_db(self, client, db):
        _vocab(db, 'ねこ', romaji='neko', meaning_de='Katze')
        before = KanaSpellScore.query.count()
        client.get('/api/practice/kana/spell/words?schrift=hiragana&source=all')
        assert KanaSpellScore.query.count() == before


class TestSpellFinishEndpoint:
    """POST /api/practice/kana/spell-finish — Persistenz + grind-sichere XP."""

    def test_requires_login(self, client, db):
        resp = client.post('/api/practice/kana/spell-finish', json={'score': 100, 'correct': 10})
        assert resp.status_code in (301, 302, 401)
        assert KanaSpellScore.query.count() == 0

    def test_saves_and_awards_xp(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/api/practice/kana/spell-finish', json={
            'schrift': 'hiragana', 'source': 'all', 'cue': 'bedeutung',
            'score': 120, 'best_streak': 8, 'correct': 18, 'misses': 2,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['saved'] is True
        # XP = Basis + min(correct, RunCap) = 3 + min(18, 15)
        assert data['xp_awarded'] == XP_STORM_BASE + XP_STORM_RUN_BONUS_CAP
        assert data['best_score'] == 120
        assert data['best_streak'] == 8
        assert data['games'] == 1
        row = KanaSpellScore.query.filter_by(user_id=user.id).first()
        assert row is not None
        assert row.score == 120 and row.correct_count == 18 and row.miss_count == 2
        assert row.source == 'all' and row.cue == 'bedeutung'
        assert db.session.get(User, user.id).total_xp == data['xp_awarded']

    def test_clamps_cheated_values(self, auth_client, db):
        client, user = auth_client
        client.post('/api/practice/kana/spell-finish', json={
            'schrift': 'bogus', 'source': 'bogus', 'cue': 'bogus',
            'score': 10 ** 9, 'best_streak': 99999, 'correct': 5, 'misses': -3,
        })
        row = KanaSpellScore.query.filter_by(user_id=user.id).first()
        assert row.score == 100000          # auf Max geclamped
        assert row.schrift == 'hiragana'    # unbekannt -> Default
        assert row.source == 'all'          # unbekannt -> Default
        assert row.cue == 'bedeutung'       # unbekannt -> Default
        assert row.miss_count == 0          # negativ -> 0
        assert row.best_streak <= row.correct_count  # Serie <= Treffer

    def test_daily_xp_cap(self, auth_client, db):
        client, user = auth_client
        granted = []
        for _ in range(6):
            d = client.post('/api/practice/kana/spell-finish', json={
                'score': 500, 'correct': 30, 'misses': 0, 'best_streak': 10,
            }).get_json()
            granted.append(d['xp_awarded'])
        assert sum(granted) == XP_STORM_DAILY_CAP
        assert granted[-1] == 0
        assert db.session.get(User, user.id).total_xp == XP_STORM_DAILY_CAP

    def test_budget_separate_from_storm(self, auth_client, db):
        # Eigenes Tages-Budget: ein ausgeschoepftes Storm-Budget nimmt dem
        # Schreibspiel KEINE XP weg (getrennte Summen-Tabellen).
        client, user = auth_client
        for _ in range(6):
            client.post('/api/practice/kana/storm-finish', json={
                'mode': 'storm', 'score': 500, 'correct': 30, 'misses': 0, 'best_combo': 10,
            })
        d = client.post('/api/practice/kana/spell-finish', json={
            'score': 100, 'correct': 18, 'misses': 0, 'best_streak': 5,
        }).get_json()
        assert d['xp_awarded'] == XP_STORM_BASE + XP_STORM_RUN_BONUS_CAP

    def test_does_not_pollute_review(self, auth_client, db):
        # Bewusste Trennung: Schreibspiel-Runden fassen weder die review-
        # semantischen Zaehler (Heatmap/Accuracy) noch FSRS an.
        client, user = auth_client
        client.post('/api/practice/kana/spell-finish', json={
            'score': 200, 'correct': 15, 'misses': 1, 'best_streak': 9,
        })
        assert DailyReviewAggregate.query.count() == 0
        assert CardReviewState.query.count() == 0


class TestSpellTab:
    """Der Schreiben-Tab ist auf /practice/kana eingebunden (gast-offen)."""

    def test_page_has_spell_tab(self, client, db):
        body = client.get('/practice/kana').get_data(as_text=True)
        assert 'kanaSpellGame(' in body
        assert 'Schreiben' in body
        assert 'かく' in body
        assert "spellPhase: 'start'" in body

    def test_deeplink_opens_spell_tab(self, client, db):
        body = client.get('/practice/kana?tab=spell').get_data(as_text=True)
        assert "game: 'spell'" in body
