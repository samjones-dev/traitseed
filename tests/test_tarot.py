"""Deck integrity and draw reproducibility."""

import random

from traitseed.tarot import FULL_DECK, draw, draw_three


def test_deck_size_and_uniqueness():
    assert len(FULL_DECK) == 78
    assert len(set(FULL_DECK)) == 78


def test_seeded_draws_are_reproducible():
    a = draw_three(rng=random.Random(42))
    b = draw_three(rng=random.Random(42))
    assert a == b


def test_different_seeds_differ():
    a = draw_three(rng=random.Random(1))
    b = draw_three(rng=random.Random(2))
    assert a != b


def test_draw_without_replacement():
    spread = draw(n=78, allow_reversed=False, rng=random.Random(7))
    names = [card.name for card in spread.cards]
    assert len(set(names)) == 78


def test_no_reversals_when_disallowed():
    spread = draw(n=10, allow_reversed=False, rng=random.Random(3))
    assert not any(card.reversed for card in spread.cards)
