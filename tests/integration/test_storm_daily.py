# tests/integration/test_storm_daily.py
"""Integration-Tests fuer das Kana-Storm-Tagesbrett (Wordle-artige Daily).

Anders als die personalisierte /daily-challenge ist /storm-daily bewusst GLOBAL:
ein Brett pro Tag, fuer ALLE Nutzer identisch (Seed nur am Datum) — sonst waere
der geteilte Wordle-Vergleich wertlos. Deckt Shape, Determinismus,
Login-Unabhaengigkeit und die teilbare /daily-Kurz-URL ab.
"""
from app.services.kana_rows import HIRAGANA_ROWS
from tests.factories import KanaFactory

GRUND_ROWS = tuple(HIRAGANA_ROWS.keys())[:11]  # vowels..n_kons (ohne Dakuten)


def _seed_hiragana(db, rows=GRUND_ROWS):
    """Legt echte Gojuon-Hiragana an (analog zu test_kana_practice_guest)."""
    created = []
    for key in rows:
        for ch in HIRAGANA_ROWS[key]:
            created.append(KanaFactory(character=ch, romanization='x', type='hiragana'))
    db.session.commit()
    return created


class TestStormDailyApi:
    """GET /api/practice/kana/storm-daily — globales Tagesbrett."""

    def test_shape(self, client, db):
        _seed_hiragana(db)
        resp = client.get('/api/practice/kana/storm-daily')
        assert resp.status_code == 200
        data = resp.get_json()
        # Erwartete Keys vorhanden.
        assert set(['kana', 'count', 'date', 'day_number']).issubset(data.keys())
        # count == len(kana) und <= 10.
        assert data['count'] == len(data['kana'])
        assert data['count'] <= 10
        # Jedes Item hat character + romanization.
        for item in data['kana']:
            assert 'character' in item
            assert 'romanization' in item

    def test_deterministic_per_day(self, client, db):
        # Zwei aufeinanderfolgende Calls -> identische Reihenfolge der Zeichen.
        _seed_hiragana(db)
        a = client.get('/api/practice/kana/storm-daily').get_json()
        b = client.get('/api/practice/kana/storm-daily').get_json()
        assert [k['character'] for k in a['kana']] == [k['character'] for k in b['kana']]

    def test_global_identical_for_guest_over_calls(self, client, db):
        # Login-unabhaengig: das Brett ist fuer den Gast ueber mehrere Calls fix.
        _seed_hiragana(db)
        boards = [
            tuple(k['character'] for k in client.get('/api/practice/kana/storm-daily').get_json()['kana'])
            for _ in range(3)
        ]
        assert len(set(boards)) == 1

    def test_logged_in_equals_guest(self, client, auth_client, db):
        # Der Seed haengt NUR am Datum (nie an user_id) -> eingeloggt == Gast.
        _seed_hiragana(db)
        guest = client.get('/api/practice/kana/storm-daily').get_json()
        auth, _user = auth_client
        loggedin = auth.get('/api/practice/kana/storm-daily').get_json()
        assert [k['character'] for k in guest['kana']] == [k['character'] for k in loggedin['kana']]


class TestDailyLanding:
    """GET /daily — teilbare Kurz-URL auf die Storm-Vollbildseite."""

    def test_renders_storm_page(self, client, db):
        resp = client.get('/daily')
        assert resp.status_code == 200
        # class="kstorm" kommt aus dem Storm-Stage-Partial (unabhaengig vom
        # Frontend-Stand des Daily-Tabs).
        assert 'class="kstorm"' in resp.get_data(as_text=True)
