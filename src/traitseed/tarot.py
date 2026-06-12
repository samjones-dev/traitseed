"""Tarot deck for symbolic seed generation.

Provides the full 78-card deck (22 Major Arcana + 56 Minor Arcana)
and a draw function that returns card names with optional reversals.

Dependency-free. Extracted from axiotic/consensus
(scripts/generate_experts/tarot.py) with one change: draws accept an
explicit ``random.Random`` so panels are reproducible from a seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Major Arcana (22 cards)
# ---------------------------------------------------------------------------

MAJOR_ARCANA: tuple[str, ...] = (
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
)

# ---------------------------------------------------------------------------
# Minor Arcana (56 cards)
# ---------------------------------------------------------------------------

SUITS: tuple[str, ...] = ("Wands", "Cups", "Swords", "Pentacles")

RANKS: tuple[str, ...] = (
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Page",
    "Knight",
    "Queen",
    "King",
)

MINOR_ARCANA: tuple[str, ...] = tuple(
    f"{rank} of {suit}" for suit in SUITS for rank in RANKS
)

FULL_DECK: tuple[str, ...] = MAJOR_ARCANA + MINOR_ARCANA


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TarotCard:
    """A tarot card with optional reversal.

    Attributes:
        name: The card name (e.g., "The Tower", "Seven of Pentacles").
        reversed: Whether the card is drawn reversed.
    """

    name: str
    reversed: bool = False

    def __str__(self) -> str:
        if self.reversed:
            return f"{self.name} (reversed)"
        return self.name


@dataclass(frozen=True)
class TarotSpread:
    """A spread of tarot cards.

    Attributes:
        cards: The cards in the spread.
    """

    cards: tuple[TarotCard, ...]

    def __str__(self) -> str:
        return ", ".join(str(card) for card in self.cards)

    def to_list(self) -> list[str]:
        return [str(card) for card in self.cards]


# ---------------------------------------------------------------------------
# Draw functions
# ---------------------------------------------------------------------------


def draw(
    n: int = 3,
    allow_reversed: bool = True,
    reversal_probability: float = 0.3,
    rng: random.Random | None = None,
) -> TarotSpread:
    """Draw n cards from the deck without replacement.

    Args:
        n: Number of cards to draw.
        allow_reversed: Whether cards can be drawn reversed.
        reversal_probability: Probability a card is reversed (if allowed).
        rng: Random source. Pass a seeded ``random.Random`` for
            reproducible draws; defaults to the module-level RNG.

    Returns:
        A TarotSpread containing the drawn cards.
    """
    if n > len(FULL_DECK):
        raise ValueError(f"Cannot draw {n} cards from a {len(FULL_DECK)}-card deck")

    rng = rng or random.Random()
    card_names = rng.sample(FULL_DECK, n)

    cards: list[TarotCard] = []
    for name in card_names:
        is_reversed = allow_reversed and rng.random() < reversal_probability
        cards.append(TarotCard(name=name, reversed=is_reversed))

    return TarotSpread(cards=tuple(cards))


def draw_three(
    allow_reversed: bool = True,
    rng: random.Random | None = None,
) -> TarotSpread:
    """Draw a three-card spread.

    The three positions are prompt scaffolding:

    1. Worldview / disposition
    2. Primary concern / focus
    3. Blind spot / shadow

    Args:
        allow_reversed: Whether cards can be drawn reversed.
        rng: Random source for reproducible draws.

    Returns:
        A TarotSpread with three cards.
    """
    return draw(n=3, allow_reversed=allow_reversed, rng=rng)
