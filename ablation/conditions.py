"""Prompt construction for the three ablation conditions.

The scaffold is identical across conditions; only the seed block varies.
See DESIGN.md. Confounds from the consensus prompt (banned names,
used-name tracking, example names, explicit vary-culture instructions)
are deliberately absent.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from traitseed.tarot import draw_three

from .traits import draw_traits

CONDITIONS = ("tarot", "none", "traits")

SCAFFOLD = """You are creating a fictional expert persona for a Delphi consultation on the question below.

Question: {question}

{seed_block}

Generate a coherent expert profile. Output as YAML with these exact fields:

```yaml
name: "Full Name with Title"
title: "Professional Title"
institution: "Institution Name"
years_experience: "Number of years of experience"
field: "Primary Field of Expertise"
formative_experiences:
  - "First key career moment that shaped their views"
  - "Second formative experience"
  - "Third experience (optional)"
persona: |
  Personality traits and communication style. How they interact
  in professional settings. Intellectual tendencies and quirks.
perspective: |
  5-10 sentence summary of how this expert approaches the question,
  what they focus on, and what they might miss.
```

The persona should feel like a real, unique individual you might encounter at a conference."""

TAROT_SEED_BLOCK = """Use these three tarot cards to shape their worldview, concerns, and blind spots:

1. Worldview/disposition: {card1}
2. Primary concern/focus: {card2}
3. Blind spot/shadow: {card3}"""

NONE_SEED_BLOCK = "Make the persona distinctive and diverse."

TRAITS_SEED_BLOCK = """Use these three randomly drawn traits to shape their worldview, concerns, and blind spots:

1. Worldview/disposition: {trait1}
2. Primary concern/focus: {trait2}
3. Blind spot/shadow: {trait3}"""


@dataclass(frozen=True)
class SeededPrompt:
    """A prompt plus the seed material that produced it."""

    condition: str
    prompt: str
    seed_material: list[str]


def build_prompt(condition: str, question: str, rng: random.Random) -> SeededPrompt:
    """Build the persona prompt for one condition.

    Args:
        condition: One of CONDITIONS.
        question: The consultation question.
        rng: Seeded random source; consumed only by tarot/traits draws.

    Returns:
        The prompt and its seed material (empty for the none condition).
    """
    if condition == "tarot":
        spread = draw_three(rng=rng)
        cards = spread.to_list()
        seed_block = TAROT_SEED_BLOCK.format(
            card1=cards[0], card2=cards[1], card3=cards[2]
        )
        seed_material = cards
    elif condition == "none":
        seed_block = NONE_SEED_BLOCK
        seed_material = []
    elif condition == "traits":
        traits = draw_traits(rng).to_list()
        seed_block = TRAITS_SEED_BLOCK.format(
            trait1=traits[0], trait2=traits[1], trait3=traits[2]
        )
        seed_material = traits
    else:
        raise ValueError(f"Unknown condition: {condition}")

    return SeededPrompt(
        condition=condition,
        prompt=SCAFFOLD.format(question=question, seed_block=seed_block),
        seed_material=seed_material,
    )
