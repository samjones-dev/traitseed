"""Invented deck: tarot's structure with no canonical symbolism.

Research baseline. Built as the control that isolates canonical
tradition from evocative structure; retained because the probes showed
most models expand these names as stably as real cards (WRITEUP.md).

22 invented majors plus 4 invented suits x the same 14 ranks. Ranks
keep their numerological priors; the suit and major semantics are the
ablated part.
"""

from __future__ import annotations

import random

from .tarot import RANKS, TarotCard, TarotSpread

FICTIONAL_MAJORS: tuple[str, ...] = (
    "The Lantern",
    "The Cartographer",
    "The Quiet Engine",
    "The Salt Road",
    "The Unfinished Bridge",
    "The Archivist",
    "The Glass Orchard",
    "The Hollow Bell",
    "The Late Harvest",
    "The Borrowed Coat",
    "The Long Stair",
    "The Paper Storm",
    "The First Frost",
    "The Threadbare Map",
    "The Second Door",
    "The Distant Signal",
    "The Folded Letter",
    "The Night Market",
    "The Empty Chair",
    "The Last Ferry",
    "The Standing Stone",
    "The Low Tide",
)

FICTIONAL_SUITS: tuple[str, ...] = ("Mirrors", "Lanterns", "Roots", "Keys")

FICTIONAL_MINORS: tuple[str, ...] = tuple(
    f"{rank} of {suit}" for suit in FICTIONAL_SUITS for rank in RANKS
)

FICTIONAL_DECK: tuple[str, ...] = FICTIONAL_MAJORS + FICTIONAL_MINORS


def draw_fictional(
    n: int = 3,
    allow_reversed: bool = True,
    reversal_probability: float = 0.3,
    rng: random.Random | None = None,
) -> TarotSpread:
    """Draw n cards from the fictional deck, mirroring tarot.draw."""
    if n > len(FICTIONAL_DECK):
        raise ValueError(
            f"Cannot draw {n} cards from a {len(FICTIONAL_DECK)}-card deck"
        )
    rng = rng or random.Random()
    card_names = rng.sample(FICTIONAL_DECK, n)
    cards = []
    for name in card_names:
        is_reversed = allow_reversed and rng.random() < reversal_probability
        cards.append(TarotCard(name=name, reversed=is_reversed))
    return TarotSpread(cards=tuple(cards))
