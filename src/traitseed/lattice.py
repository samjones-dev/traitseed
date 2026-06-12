"""Curated trait lattices: the validated seed system.

A Lattice is an ordered set of positions (worldview / concern /
blind spot by default), each holding a curated item list. A draw picks
one item per position with a seeded RNG and optional intensity flags,
returning a Seed that carries its own provenance.

Evidence (see WRITEUP.md): curated lattices beat canonical symbol
decks, random words, and naive diversity prompting on coherence,
plausibility, blind-spot quality, and embedding dispersion, across
every generator tested. Lattice authorship is robust — frontier-model
and human-taxonomy lattices measure equivalent.

    from traitseed import Lattice
    import random

    lattice = Lattice.default()
    seed = lattice.draw(rng=random.Random(42))
    prompt = f"Create a character study.\\n\\n{seed.block()}"
    record = seed.to_dict()   # persist alongside the artefact
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

DEFAULT_INTENSITY_PROBABILITY = 0.3


@dataclass(frozen=True)
class Position:
    """One lattice position: a name, a display label, and its items.

    Attributes:
        name: Machine name (e.g. "blind_spot").
        label: Label used in seed blocks (e.g. "Blind spot/shadow").
        items: The curated item list.
        intensity_suffix: Appended (parenthesised) when a draw
            intensifies this position; None disables intensification.
    """

    name: str
    label: str
    items: tuple[str, ...]
    intensity_suffix: str | None = None

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError(f"Position {self.name!r} has no items")
        if len(set(self.items)) != len(self.items):
            raise ValueError(f"Position {self.name!r} has duplicate items")


@dataclass(frozen=True)
class SeedItem:
    """One drawn item with its intensification state."""

    position: str
    label: str
    base: str
    intensified: bool
    text: str

    @classmethod
    def make(cls, position: Position, base: str, intensified: bool) -> SeedItem:
        text = base
        if intensified and position.intensity_suffix:
            text = f"{base} ({position.intensity_suffix})"
        return cls(
            position=position.name,
            label=position.label,
            base=base,
            intensified=intensified,
            text=text,
        )


@dataclass(frozen=True)
class Seed:
    """A drawn seed: one item per position, plus provenance.

    Attributes:
        lattice: Name of the lattice this seed was drawn from.
        items: The drawn items in position order.
    """

    lattice: str
    items: tuple[SeedItem, ...]

    def to_list(self) -> list[str]:
        return [item.text for item in self.items]

    def block(self) -> str:
        """Numbered seed block for prompt scaffolding."""
        return "\n".join(
            f"{i + 1}. {item.label}: {item.text}"
            for i, item in enumerate(self.items)
        )

    def to_dict(self) -> dict:
        """Provenance record for persisting alongside the artefact."""
        return {
            "lattice": self.lattice,
            "items": [
                {
                    "position": item.position,
                    "base": item.base,
                    "intensified": item.intensified,
                    "text": item.text,
                }
                for item in self.items
            ],
        }


@dataclass(frozen=True)
class Lattice:
    """A curated trait lattice.

    Attributes:
        name: Lattice identifier, recorded in every Seed it draws.
        positions: Ordered positions, each with its item list.
        provenance: Where the items came from.
    """

    name: str
    positions: tuple[Position, ...]
    provenance: str = ""

    def draw(
        self,
        rng: random.Random | None = None,
        intensity_probability: float = DEFAULT_INTENSITY_PROBABILITY,
    ) -> Seed:
        """Draw one item per position.

        Args:
            rng: Random source. Pass a seeded ``random.Random`` for
                reproducible draws.
            intensity_probability: Per-position chance the item is
                marked with the position's intensity suffix.

        Returns:
            A Seed carrying the drawn items and lattice name.
        """
        rng = rng or random.Random()
        items = []
        for position in self.positions:
            base = rng.choice(position.items)
            intensified = (
                position.intensity_suffix is not None
                and rng.random() < intensity_probability
            )
            items.append(SeedItem.make(position, base, intensified))
        return Seed(lattice=self.name, items=tuple(items))

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provenance": self.provenance,
            "positions": [
                {
                    "name": p.name,
                    "label": p.label,
                    "intensity_suffix": p.intensity_suffix,
                    "items": list(p.items),
                }
                for p in self.positions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Lattice:
        return cls(
            name=data["name"],
            provenance=data.get("provenance", ""),
            positions=tuple(
                Position(
                    name=p["name"],
                    label=p["label"],
                    items=tuple(p["items"]),
                    intensity_suffix=p.get("intensity_suffix"),
                )
                for p in data["positions"]
            ),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=1) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> Lattice:
        return cls.from_dict(json.loads(Path(path).read_text()))

    # -- bundled lattices --------------------------------------------------

    @classmethod
    def bundled(cls, name: str) -> Lattice:
        """Load a lattice shipped with the package.

        Available names: see :func:`list_bundled`.
        """
        ref = resources.files("traitseed").joinpath("lattices", f"{name}.json")
        try:
            return cls.from_dict(json.loads(ref.read_text()))
        except FileNotFoundError:
            raise ValueError(
                f"No bundled lattice {name!r}; available: {list_bundled()}"
            ) from None

    @classmethod
    def default(cls) -> Lattice:
        """The most-tested bundled lattice (claude-traits)."""
        return cls.bundled("claude-traits")


def list_bundled() -> list[str]:
    """Names of lattices shipped with the package."""
    return sorted(
        ref.name.removesuffix(".json")
        for ref in resources.files("traitseed").joinpath("lattices").iterdir()
        if ref.name.endswith(".json")
    )
