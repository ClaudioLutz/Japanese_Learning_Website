"""Registrierungs-/Login-Schutz: Rate-Limit, Honeypot, Username-Muster.

Der Limiter ist in Tests global aus (siehe tests/conftest.py). Nur die Tests in
diesem Modul schalten ihn ueber die Fixture `limited` gezielt ein.
"""

import logging

import pytest

from app import client_ip
from app.models import User


@pytest.fixture
def limited(rate_limited):
    """Alias auf die globale Fixture `rate_limited` (tests/conftest.py)."""
    return rate_limited


def _reg_payload(n=0, website=''):
    return {
        'username': f'neuling{n}',
        'email': f'neuling{n}@example.com',
        'password': 'Passwort1',
        'password2': 'Passwort1',
        'website': website,
    }


# ── Rate-Limit ────────────────────────────────────────────────────────────


def test_register_429_nach_fuenf_versuchen(client, limited):
    """Der 6. Registrierungs-POST derselben IP innerhalb einer Stunde -> 429."""
    headers = {'CF-Connecting-IP': '203.0.113.10'}
    codes = [
        client.post('/register', data=_reg_payload(i), headers=headers).status_code
        for i in range(6)
    ]
    assert codes[:5].count(429) == 0, f'Zu frueh limitiert: {codes}'
    assert codes[5] == 429, f'6. Versuch haette 429 sein muessen: {codes}'


def test_register_429_zeigt_deutsche_seite(client, limited):
    headers = {'CF-Connecting-IP': '203.0.113.11'}
    for i in range(5):
        client.post('/register', data=_reg_payload(i), headers=headers)
    resp = client.post('/register', data=_reg_payload(99), headers=headers)
    assert resp.status_code == 429
    body = resp.get_data(as_text=True)
    assert 'Kurz durchatmen' in body
    assert '<html' in body.lower()  # gerendertes Template, kein nacktes Text-429


def test_register_limit_trennt_nach_cf_connecting_ip(client, limited):
    """Zwei verschiedene Client-IPs hinter demselben Tunnel teilen kein Kontingent."""
    for i in range(6):
        client.post('/register', data=_reg_payload(i),
                    headers={'CF-Connecting-IP': '203.0.113.20'})
    # Erste IP ist erschoepft ...
    assert client.post('/register', data=_reg_payload(50),
                       headers={'CF-Connecting-IP': '203.0.113.20'}).status_code == 429
    # ... die zweite IP nicht.
    assert client.post('/register', data=_reg_payload(51),
                       headers={'CF-Connecting-IP': '198.51.100.7'}).status_code != 429


def test_register_get_zaehlt_nicht_aufs_limit(client, limited):
    headers = {'CF-Connecting-IP': '203.0.113.30'}
    for _ in range(10):
        assert client.get('/register', headers=headers).status_code == 200


def test_login_429_nach_zehn_versuchen(client, limited):
    headers = {'CF-Connecting-IP': '203.0.113.40'}
    data = {'email': 'nobody@example.com', 'password': 'Falsch123'}
    codes = [client.post('/login', data=data, headers=headers).status_code for _ in range(11)]
    assert codes[:10].count(429) == 0, f'Zu frueh limitiert: {codes}'
    assert codes[10] == 429, f'11. Versuch haette 429 sein muessen: {codes}'


def test_forgot_password_429_nach_fuenf_versuchen(client, limited):
    headers = {'CF-Connecting-IP': '203.0.113.50'}
    data = {'email': 'nobody@example.com'}
    codes = [
        client.post('/forgot-password', data=data, headers=headers).status_code
        for _ in range(6)
    ]
    assert codes[5] == 429, f'6. Versuch haette 429 sein muessen: {codes}'


# ── Key-Funktion ──────────────────────────────────────────────────────────


def test_client_ip_bevorzugt_cf_connecting_ip(app):
    with app.test_request_context(
        '/', headers={'CF-Connecting-IP': '9.9.9.9', 'X-Forwarded-For': '1.1.1.1, 2.2.2.2'},
        environ_base={'REMOTE_ADDR': '10.0.0.1'},
    ):
        assert client_ip() == '9.9.9.9'


def test_client_ip_faellt_auf_xff_erstes_element(app):
    with app.test_request_context(
        '/', headers={'X-Forwarded-For': '1.1.1.1, 2.2.2.2'},
        environ_base={'REMOTE_ADDR': '10.0.0.1'},
    ):
        assert client_ip() == '1.1.1.1'


def test_client_ip_faellt_auf_remote_addr(app):
    """Tests/lokal ohne Proxy-Header: sauberer Fallback, kein Crash."""
    with app.test_request_context('/', environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        assert client_ip() == '10.0.0.1'


# ── Honeypot ──────────────────────────────────────────────────────────────


def test_honeypot_gefuellt_legt_keinen_user_an(client, db, caplog):
    with caplog.at_level(logging.WARNING):
        resp = client.post('/register', data=_reg_payload(1, website='http://spam.example'))
    assert resp.status_code == 302  # Redirect wie ein normaler Formular-Abschluss
    assert User.query.filter_by(username='neuling1').first() is None
    assert any(r.levelno >= logging.WARNING and 'Honeypot' in r.getMessage()
               for r in caplog.records), 'WARNING-Log zum Honeypot fehlt'


def test_honeypot_leer_legt_user_an(client, db):
    resp = client.post('/register', data=_reg_payload(2), follow_redirects=False)
    assert resp.status_code == 302
    assert User.query.filter_by(username='neuling2').first() is not None


def test_honeypot_feld_ist_im_html_und_nicht_type_hidden(client):
    body = client.get('/register').get_data(as_text=True)
    assert 'name="website"' in body
    assert 'hp-field' in body
    assert 'tabindex="-1"' in body
    assert 'aria-hidden="true"' in body
    # Per CSS versteckt, nicht per type=hidden
    assert 'type="hidden" name="website"' not in body


# ── Username-Validierung ──────────────────────────────────────────────────


@pytest.mark.parametrize('bad', [
    '<script>',
    'a<b',
    'a>b',
    'ab',                  # zu kurz
    'x' * 33,              # zu lang
    'mit leerzeichen',
    'email@example.com',
    'süss',                # Nicht-ASCII
])
def test_ungueltiger_username_wird_abgelehnt(client, db, bad):
    resp = client.post('/register', data={
        'username': bad,
        'email': 'gueltig@example.com',
        'password': 'Passwort1',
        'password2': 'Passwort1',
        'website': '',
    })
    assert resp.status_code == 200  # Formular mit Fehler neu gerendert
    assert User.query.filter_by(email='gueltig@example.com').first() is None


@pytest.mark.parametrize('good', ['abc', 'Claudio_86', 'a.b-c', 'x' * 32])
def test_gueltiger_username_wird_akzeptiert(client, db, good):
    resp = client.post('/register', data={
        'username': good,
        'email': 'gueltig@example.com',
        'password': 'Passwort1',
        'password2': 'Passwort1',
        'website': '',
    })
    assert resp.status_code == 302
    assert User.query.filter_by(username=good).first() is not None
