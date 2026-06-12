"""Seeding for varied, coherent LLM data generation.

Primary interface: curated trait lattices (the validated method).
Baselines retained for research: the tarot deck the project began
with, and the invented deck used as its control. See WRITEUP.md.
"""

from traitseed.author import AuthoringError, author_lattice
from traitseed.fictional import FICTIONAL_DECK, draw_fictional
from traitseed.lattice import (
    Lattice,
    Position,
    Seed,
    SeedItem,
    list_bundled,
)
from traitseed.tarot import (
    FULL_DECK,
    MAJOR_ARCANA,
    MINOR_ARCANA,
    TarotCard,
    TarotSpread,
    draw,
    draw_three,
)

__version__ = "0.1.0"

__all__ = [
    # lattices (primary)
    "Lattice",
    "Position",
    "Seed",
    "SeedItem",
    "list_bundled",
    "author_lattice",
    "AuthoringError",
    # decks (research baselines)
    "FULL_DECK",
    "MAJOR_ARCANA",
    "MINOR_ARCANA",
    "TarotCard",
    "TarotSpread",
    "draw",
    "draw_three",
    "FICTIONAL_DECK",
    "draw_fictional",
]
