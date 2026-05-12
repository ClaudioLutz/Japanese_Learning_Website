"""Tests fuer Variable XP-Boost (Phase 2)."""
import random

from app.gamification_service import (
    XP_BOOST_MAX,
    XP_BOOST_MIN,
    XP_BOOST_PROBABILITY,
    maybe_grant_random_xp_boost,
)


def test_no_boost_when_rng_above_probability():
    """rng.random() ueber Schwelle => kein Boost."""
    class _MockRng:
        def random(self):
            return XP_BOOST_PROBABILITY + 0.01
        def randint(self, a, b):
            return 999  # falls trotzdem aufgerufen, fail
    assert maybe_grant_random_xp_boost(rng=_MockRng()) == 0


def test_boost_when_rng_below_probability():
    """rng.random() unter Schwelle => Boost wird returnt."""
    class _MockRng:
        def random(self):
            return 0.001
        def randint(self, a, b):
            assert a == XP_BOOST_MIN and b == XP_BOOST_MAX
            return 17
    assert maybe_grant_random_xp_boost(rng=_MockRng()) == 17


def test_montecarlo_probability_in_range():
    """Ueber 5'000 Trials soll die Boost-Quote nahe XP_BOOST_PROBABILITY liegen."""
    rng = random.Random(42)  # deterministisch fuer CI
    trials = 5000
    boosts = sum(1 for _ in range(trials) if maybe_grant_random_xp_boost(rng=rng) > 0)
    observed = boosts / trials
    # ±2 Prozentpunkte Toleranz
    assert abs(observed - XP_BOOST_PROBABILITY) < 0.02, \
        f'observed={observed:.4f}, expected={XP_BOOST_PROBABILITY:.4f}'


def test_boost_value_within_min_max():
    """Wenn Boost faellt, liegt der Wert zwischen MIN und MAX."""
    rng = random.Random(0)
    for _ in range(2000):
        b = maybe_grant_random_xp_boost(rng=rng)
        if b > 0:
            assert XP_BOOST_MIN <= b <= XP_BOOST_MAX
