"""Author a domain-tuned lattice from a brief, via any LLM callable.

Provider-agnostic: pass any ``Callable[[str], str]`` that sends a
prompt and returns the completion text. Authorship is robust — in the
T7L controls, lattices written by different frontier models from the
same brief measured equivalent (see WRITEUP.md) — so use whichever
model you have.

    from traitseed import author_lattice

    def llm(prompt: str) -> str:
        ...  # your provider call

    lattice = author_lattice(
        "generating diverse fictional clinicians for triage simulations",
        llm,
        name="clinicians-v1",
    )
    lattice.save("clinicians-v1.json")
"""

from __future__ import annotations

import re
from typing import Callable

from .lattice import Lattice, Position

DEFAULT_ITEMS = 78

# Position briefs mirror the ones used (verbatim apart from the domain
# slot) to author the validated gpt41-traits lattice.
DEFAULT_POSITION_BRIEFS: tuple[tuple[str, str, str, str], ...] = (
    (
        "worldview",
        "Worldview/disposition",
        "taken to excess",
        "distinct one-or-two-word worldview/disposition descriptors "
        "(e.g. the style of 'pragmatic', 'risk-averse', 'locally rooted')",
    ),
    (
        "concern",
        "Primary concern/focus",
        "to the point of obsession",
        "distinct short concern/focus topics, specific to the domain "
        "(e.g. the style of 'equity of access', 'vendor lock-in')",
    ),
    (
        "blind_spot",
        "Blind spot/shadow",
        "severe",
        "distinct short blind-spot/flaw phrases "
        "(e.g. the style of 'mistaking pilots for proof', 'overvaluing novelty')",
    ),
)

AUTHOR_PROMPT = """You are curating seed material for {brief}. Write a list of exactly {n} {position_brief}.

Requirements: all items distinct, no numbering, plain lowercase, one item per line, exactly {n} lines, no other text."""


class AuthoringError(RuntimeError):
    """The LLM callable could not produce a valid item list."""


def _parse_items(raw: str, n: int) -> list[str] | None:
    lines = [re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip() for line in raw.splitlines()]
    unique = list(dict.fromkeys(line for line in lines if line))
    if len(unique) >= n:
        return unique[:n]
    return None


def author_lattice(
    brief: str,
    llm: Callable[[str], str],
    *,
    name: str,
    items_per_position: int = DEFAULT_ITEMS,
    position_briefs: tuple[tuple[str, str, str, str], ...] = DEFAULT_POSITION_BRIEFS,
    max_attempts: int = 3,
) -> Lattice:
    """Author a lattice for a domain brief.

    Args:
        brief: What the lattice will seed, e.g. "generating diverse
            fictional clinicians for triage simulations".
        llm: Callable that takes a prompt and returns completion text.
        name: Lattice name, recorded in every seed it draws.
        items_per_position: List length per position. 78 matches the
            validated draw entropy; shorter lists trade coverage.
        position_briefs: (name, label, intensity_suffix, item brief)
            per position. Defaults to the validated three positions.
        max_attempts: LLM attempts per position before failing.

    Returns:
        The authored Lattice.

    Raises:
        AuthoringError: If any position list cannot be produced.
    """
    positions = []
    for pos_name, label, suffix, pos_brief in position_briefs:
        prompt = AUTHOR_PROMPT.format(
            brief=brief, n=items_per_position, position_brief=pos_brief
        )
        items = None
        for _ in range(max_attempts):
            items = _parse_items(llm(prompt), items_per_position)
            if items:
                break
        if not items:
            raise AuthoringError(
                f"Could not produce {items_per_position} distinct items "
                f"for position {pos_name!r} in {max_attempts} attempts"
            )
        positions.append(
            Position(
                name=pos_name,
                label=label,
                items=tuple(items),
                intensity_suffix=suffix,
            )
        )
    return Lattice(
        name=name,
        positions=tuple(positions),
        provenance=f"Authored from brief: {brief!r}",
    )
