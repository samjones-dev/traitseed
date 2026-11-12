# Traitseed

[![test](https://github.com/samjones-dev/traitseed/actions/workflows/test.yml/badge.svg)](https://github.com/samjones-dev/traitseed/actions/workflows/test.yml)

Reproducible diversity for LLM data generation. Seed every generation
with a draw from a curated trait lattice and get varied, coherent,
traceable output.

```python
from traitseed import Lattice
import random

lattice = Lattice.default()
seed = lattice.draw(rng=random.Random(42))

print(seed.block())
# 1. Worldview/disposition: futurist (taken to excess)
# 2. Primary concern/focus: market dynamics (to the point of obsession)
# 3. Blind spot/shadow: trusting self-reported data

prompt = f"Create a fictional expert persona.\n\n{seed.block()}"
record = seed.to_dict()   # persist with the artefact: full provenance
```

Zero dependencies. MIT.

## Why

LLMs collapse under "be diverse" prompting: ask for twelve personas
and you get the same worldview, the same concerns, the same hedged
style, at any temperature. traitseed replaces the diversity
instruction with a sampled seed, one item per position (worldview,
concern, blind spot) drawn from curated 78-item trait lists.

- **Varied**: ~2 million distinct seeds per lattice; measured highest
  embedding dispersion of any seeding strategy tested.
- **Coherent**: curated items keep characters psychologically
  consistent; random words measurably do not.
- **Reproducible**: pass a seeded `random.Random`, persist
  `seed.to_dict()`, and any panel can be regenerated exactly.
- **Productively flawed**: the blind-spot position gives each persona
  a genuine, specific weakness — what makes synthetic panels disagree
  instead of converging.

One honest scope note: **names are a separate failure mode.** Our
measurements show semantic seeding barely moves name repetition ("Dr
Aris Thorne" survives every seed). Pair traitseed with an explicit
name list or post-generation dedup if you need unique names.

## Install

```
pip install traitseed
```

Or from source: `pip install git+https://github.com/samjones-dev/traitseed`.

## Bundled lattices

Three generic lattices ship with the package. They measured statistically
equivalent in testing, pick any:

| name | author |
|---|---|
| `claude-traits` (default) | Claude (Anthropic) |
| `gpt41-traits` | GPT-4.1 (OpenAI) |
| `human-taxonomies` | Big-Five markers, Rokeach/Schwartz values, named cognitive biases |

```python
from traitseed import Lattice, list_bundled

list_bundled()                        # ['claude-traits', 'gpt41-traits', 'human-taxonomies']
lattice = Lattice.bundled("human-taxonomies")
```

## Author a domain-tuned lattice

Generic lattices seed generic personas. For a specific domain, author
a lattice once with any LLM and reuse it forever:

```python
from traitseed import author_lattice

def llm(prompt: str) -> str:
    ...  # any provider — return the completion text

lattice = author_lattice(
    "generating diverse fictional clinicians for triage simulations",
    llm,
    name="clinicians-v1",
)
lattice.save("clinicians-v1.json")     # commit it; Lattice.load() to reuse
```

Lattice authorship is robust: in testing, lattices written by
different frontier models from the same brief performed identically.

## How it works

A `Lattice` is an ordered set of positions, each holding a curated
item list. `draw()` picks one item per position with your RNG; ~30% of
items get an intensity flag ("taken to excess") that mirrors how a
trait distorts under pressure. The returned `Seed` renders a numbered
prompt block and serialises to a provenance record.

Custom positions, list sizes, and intensity suffixes are all plain
constructor arguments: see `traitseed.lattice`.

## Evidence

The design is measured. Across 18 models, ~26k generations,
pre-registered decision rules, and blind cross-family judging, curated
trait lattices were simultaneously the most coherent, most plausible,
best on blind-spot quality, and most dispersed. Against every
baseline tested: symbolic decks, an invented deck, random words, and
naive diversity prompting. There is no varied-versus-coherent
trade-off with good seeds.

Full write-up: [WRITEUP.md](WRITEUP.md). Designs, run artefacts, and
verdict grids: [`ablation/`](ablation/) and [`probes/`](probes/)
(`uv run python -m probes.aggregate` reproduces the tables).

## Baselines

The symbolic decks the evaluation grew from remain available
(`traitseed.tarot`, `traitseed.fictional`) — useful as baselines for
your own seeding experiments, and the foundation the lattice design
inherited its scaffold and draw entropy from.

## Licence

MIT.
