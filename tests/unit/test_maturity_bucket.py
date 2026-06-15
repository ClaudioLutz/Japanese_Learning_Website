"""Unit-Tests fuer den kanonischen Reife-Bucket-Mapper (Single Source).

maturity_bucket(status, stage_idx) ist die EINZIGE Quelle fuer die 5-Bucket-
Einteilung [Neu, Lernen, Jung, Reif, Gemeistert], aus der sowohl der N5-Kompass-
Ring als auch der Reife-Tab ableiten. Spiegelt die Logik von
srs_service.get_maturity_distribution.
"""
import pytest

from app.gamification_service import MATURITY_BUCKETS, maturity_bucket


def test_buckets_have_five_labels():
    assert MATURITY_BUCKETS == ('Neu', 'Lernen', 'Jung', 'Reif', 'Gemeistert')


def test_suspended_returns_none():
    # Suspendierte Karten zaehlt der Aufrufer separat -> None.
    assert maturity_bucket('suspended', 5) is None
    assert maturity_bucket('suspended', 0) is None


@pytest.mark.parametrize('status', ['learning', 'relearning'])
def test_learning_states_map_to_lernen(status):
    # Lern-/Relearn-Status schlaegt die Stufe (egal welcher stage_idx).
    assert maturity_bucket(status, 0) == 1
    assert maturity_bucket(status, 9) == 1


@pytest.mark.parametrize('stage_idx,expected', [
    (0, 0),   # Neu
    (1, 2), (4, 2),         # Jung (stage 1..4)
    (5, 3), (6, 3),         # Reif (stage 5..6)
    (7, 4), (9, 4),         # Gemeistert (stage 7+)
])
def test_review_stage_mapping(stage_idx, expected):
    assert maturity_bucket('review', stage_idx) == expected


def test_index_resolves_to_label():
    # Jeder zurueckgegebene Index ist ein gueltiger Label-Index.
    for status, stage in [('review', 0), ('review', 3), ('review', 6), ('review', 8), ('learning', 2)]:
        idx = maturity_bucket(status, stage)
        assert 0 <= idx < len(MATURITY_BUCKETS)
