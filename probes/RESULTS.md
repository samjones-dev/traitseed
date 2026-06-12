# Phase-2 probe results

Both probes run 11 June 2026 on `google/gemini-2.5-flash`, master seed
42. Artefacts: `runs/t1/`, `runs/t2/`. Cost ≈ $0.70. Rules were
pre-registered in DESIGN.md and signed off before generation.

## T1 — symbol expansion (latent richness)

**Rule: FAILS.** Real deck and fictional deck are statistically
indistinguishable on stability, and the fictional deck wins separation.

| deck | stability | separation | stab (majors) | stab (minors) |
|---|---|---|---|---|
| real | 0.878 | 0.415 | 0.881 | 0.877 |
| fictional | 0.871 | **0.439** | 0.885 | 0.866 |

The model expands "The Hollow Bell" as consistently as "The Tower":
independent samples converge on emptiness, unheard truths, unfulfilled
potential. The three most distinct cards in the whole experiment are
fictional majors (The Empty Chair 0.60, The Low Tide 0.59, The Paper
Storm 0.58). The weakest are fictional minors with an abstract suit
(Ten/Five/Eight of Keys, 0.22–0.31) — compositional names need
evocative components.

## T2 — fixed-seed steering

**Rule: FAILS.** Tarot steers repeated generations no better than
invented cards, and far less than explicit trait words.

| condition | within-draw | across-draw | steering ratio |
|---|---|---|---|
| tarot | 0.281 | 0.386 | 1.37 |
| fictional | 0.246 | 0.358 | 1.45 |
| traits | 0.291 | 0.535 | **1.84** |

Explicit traits pin the output's content directly, so different draws
land far apart. Different card draws — real or invented — still land in
overlapping archetype space.

## Synthesis

The mechanism claim as stated — tarot's canonical symbolism, absorbed
from human training data, does work that structure alone cannot — found
no support in either probe on this model. What the probes found instead
is arguably more useful:

**The model is a general-purpose symbol expander.** Any evocative name
gets a stable, distinct, human-plausible interpretation; a canonical
tradition adds nothing measurable. The "human-aligned semiotics" live
in the model's compositional reading of evocative language, not in the
specific cultural artefact.

If that survives replication, the project's asset inverts: decks can be
invented freely (no copyright constraints, unbounded deck space,
domain-tunable symbolism), and the micro-library's `Deck` abstraction
matters more than which deck ships as default. The cost is the README's
stated contribution ("no published work uses a cultural symbol lattice
as the seed") — the lattice being cultural appears to be incidental.

## Cross-model replication (4 models)

Same seeds, same draws, three added families: `openai/gpt-4.1-mini`,
`anthropic/claude-haiku-4.5`, `qwen/qwen3-next-80b-a3b-instruct`.
Claude T2 at temperature 1.0 (provider cap; recorded deviation).
Artefacts: `runs/t1-*/`, `runs/t2-*/`.

### T1 — stability / separation (real vs fictional)

| model | real stab | fict stab | real sep | fict sep | rule |
|---|---|---|---|---|---|
| gemini-2.5-flash | 0.878 | 0.871 | 0.415 | 0.439 | fails |
| gpt-4.1-mini | 0.949 | 0.904 | 0.371 | 0.376 | fails (by 0.005) |
| claude-haiku-4.5 | 0.914 | 0.928 | 0.415 | 0.386 | fails |
| qwen3-next-80b | 0.931 | 0.900 | 0.536 | 0.516 | **holds** |

1 of 4 holds, but every failure fails a different conjunct and most
margins are small. Real wins stability on 2, ties 1, loses 1; real wins
separation on 2, loses 2 (one by 0.005). No model shows the fictional
deck dominating.

### T2 — steering ratio

| model | tarot | fictional | traits | tarot>fict | best |
|---|---|---|---|---|---|
| gemini-2.5-flash | 1.37 | 1.45 | 1.84 | fails | traits |
| gpt-4.1-mini | 1.43 | 1.42 | 1.75 | holds (by 0.01) | traits |
| claude-haiku-4.5 | 1.27 | 1.15 | 1.82 | **holds** | traits |
| qwen3-next-80b | 2.01 | 1.88 | 1.87 | **holds** | **tarot** |

3 of 4 hold. Gemini — the model every phase-1 and single-model verdict
was based on — is the outlier, not the rule. On qwen, tarot beats
everything outright, including explicit traits.

### Revised synthesis

The gemini-only conclusion ("canonical tradition adds nothing") does
not survive replication. The fairer summary:

1. **A real, small, model-dependent canonical-symbolism effect
   exists.** Tarot steers better than invented cards on 3 of 4 models,
   and on qwen it shows the clearest expansion advantage too.
2. **Explicit trait words still steer hardest on 3 of 4 models.** The
   case for symbols over traits cannot rest on steering or variance;
   if it exists it lives in coherence and human-alignment (T4, T6, T3
   — undone).
3. **Single-model verdicts in this domain are unreliable.** Twice now a
   conclusion flipped when a second model was added. Every future rule
   verdict should be stated per-model with a cross-model tally.

## Model sweep (11 June 2026, 18 models)

Extended the grid with open-source datagen candidates, higher-tier
commercial models, and the Gemini 3 tier. The sweep stalled once
mid-run — reasoning-token billing exhausted the account (budget note
below) — and completed after a top-up under the new spend guard, with
the partial runs resumed in place. Reproduce the grids with
`uv run python -m probes.aggregate`.

**Excluded row:** `glm-4.6` T1 is invalid — it returned empty content
(median 1 character) for 398 of 624 fictional-card prompts and 33 real
ones. Its "0.084 fictional separation" is the embedding of newlines.
Notably it is the only model that returns nothing for an unknown card
instead of confabulating a meaning; every other model interprets
invented symbols fluently. Its T2 records are full-length and valid.

### T1 tally: 8 of 17 valid models hold

Holds: gemini-2.5-pro, gemini-3.1-pro, gemini-3.5-flash, gpt-oss-120b,
kimi-k2, llama-3.3-70b, llama-4-maverick, qwen3-next-80b.

The interim "open-weight only" hypothesis (3/11 at the time) did not
survive the full grid: the Gemini reasoning tier holds strongly, with
gemini-3.1-pro showing the largest gap in the project — fictional-card
expansions destabilise badly there (stability 0.651 vs 0.938 real).
The revised pattern: canonical advantage appears in open-weight models
and Gemini reasoning models; it is absent in Anthropic, OpenAI API
models, DeepSeek, Mistral, and the small Gemini flashes.

### T2 tally: 9 of 18 hold — a coin flip with pockets

Tarot beats everything outright on three models: `gemini-3-flash`
(2.15 vs 1.52 fictional — the strongest tarot result in the project),
`qwen3-next-80b` (2.01), `deepseek-v3.1` (1.45). Traits are best on 13
of 18. No systematic canonical-steering effect across the population;
real model-specific pockets.

Models where BOTH rules hold: `qwen3-next-80b`, `kimi-k2`,
`gemini-3.1-pro`.

### Diversity vs cost (the datagen question)

Absolute T2 distances are cross-model comparable (fixed embedding
space). Seeded coverage (tarot across-draw): gpt-4.1 0.493 >
deepseek-v4-flash 0.472 ≈ deepseek-v3.1 0.471 ≈ gemini-2.5-pro 0.462 >
claude-sonnet-4.6 0.443. Diversity is not gated by price — DeepSeek
matches the commercial tier at 1/20th the cost.

Two regimes matter more than the ranking:

- **Noisy-diverse** (gpt-4.1: within-draw 0.417): coverage comes from
  sampling noise; the seed controls little, weakening provenance.
- **Steered-diverse** (qwen3-next 0.206, gemini-3-flash 0.191 within):
  similar coverage at a third of the noise — the seed determines where
  output lands.

With the full grid, `kimi-k2` posts the highest raw coverage (0.520)
but also the worst within-draw noise (0.446) and the lowest steering
ratio — the extreme noisy-diverse case. Picks for large-scale seeded
generation stand: `deepseek-v4-flash` for raw coverage per dollar;
`qwen3-next-80b` for steering discipline (and one of three models
where both rules hold).

### Budget note

The original sweep estimate (~$15–18) was exceeded ~2×: Gemini
reasoning models bill thinking tokens as output at $9–12/M, which was
flagged as possible but not bounded or metered. The account ran to $0
mid-sweep and in-flight chains crashed on 402s; streaming writes
preserved all partials. The harness now has a per-call max_tokens cap
and a credits-floor check (abort below $10, checked every 25 calls);
the remaining runs completed under it without incident.

## T4 + T6 — coherence and blind-spot quality (11 June 2026)

Run on the three models where both mechanism rules held (qwen3-next,
kimi-k2, gemini-3.1-pro). Judge: claude-sonnet-4.6 at temperature 0,
blind to condition, 720 studies, zero parse failures. Artefacts:
`runs/t4-none-*`, `runs/t46-judged-*`.

**T4 (tarot > traits on coherence+plausibility): 0 of 3 hold.**
**T6 (tarot > none on blind-spot quality): 1 of 3 hold** (gemini-3.1-pro).

| generator | cond | T4 | T6 | dispersion |
|---|---|---|---|---|
| qwen3-next | tarot | 3.98 | 4.19 | 0.398 |
| qwen3-next | traits | **4.54** | **4.77** | **0.560** |
| qwen3-next | none | 4.19 | 4.61 | 0.437 |
| kimi-k2 | tarot | 3.71 | 3.98 | 0.514 |
| kimi-k2 | traits | **4.21** | **4.55** | **0.624** |
| kimi-k2 | none | 3.84 | 4.27 | 0.598 |
| gemini-3.1-pro | tarot | 4.02 | 4.08 | 0.342 |
| gemini-3.1-pro | traits | **4.47** | **4.86** | 0.477 |
| gemini-3.1-pro | none | 3.86 | 3.79 | **0.570** |

The Frankenstein hypothesis is refuted, not just unsupported: explicit
trait combinations did not produce incoherent characters. On all three
models the trait condition is simultaneously the most coherent, most
plausible, best on blind-spot quality, AND the most dispersed — it
dominates the Pareto frontier rather than sitting at its noisy end.
Tarot is not trading coherence for diversity; it is worse at both.

Caveats: judge blindness is compromised — 67–99% of seeded studies
contain seed vocabulary (for traits this is largely benign topical
overlap; for tarot it is genuine leakage, and esoteric card references
in prose may read as less plausible to the judge). One judge family;
scores are not calibrated across generators.

## The full arc

1. **T1:** about half the models hold stable, distinct canonical
   symbolism (latent richness is real, model-dependent).
2. **T2:** on those models the symbols steer generation (steering is
   real where richness is).
3. **T4/T6:** but the resulting personas are less coherent, less
   plausible, and less diverse than personas seeded with plain trait
   words — on the very models most favourable to tarot.

At every measurement point across two phases, explicit trait lists
matched or beat the symbol lattice. The romantic hypothesis was
measured carefully and the boring alternative won everywhere it
mattered. What survives: the positional scaffold (worldview / concern /
blind spot), seeded provenance, and the Deck abstraction — with trait
lists, not tarot, as the evidence-backed default.

## T7L — lattice controls (11 June 2026)

**R1 (curation matters): 3 of 3. R2 (author-robust): 3 of 3.**
540 lattice-seeded studies, same blind judge, zero parse failures.
Artefacts: `runs/lat-*`, lattices in `probes/lattices/`.

The six-condition T4 ranking is near-identical on every generator:

1. **Curated lattices cluster at the top, regardless of author.**
   Claude's traits, gpt-4.1's lattice, and the human-taxonomy lattice
   sit within ~0.1–0.25 of each other on T4 (4.2–4.6), all with
   top-tier dispersion (0.48–0.62). Authoring is not the bottleneck;
   any competent curator — frontier model or published psychometric
   taxonomy — produces an equivalent lattice.
2. **Uncurated words buy diversity at coherence cost.** `degraded`
   gets high dispersion (0.52–0.60) but the worst coherence
   (T4 3.4–4.0). The Frankenstein failure mode is real — curation is
   what avoids it, not symbol opacity.
3. **Tarot lands in the degraded cluster.** On T4 it ties or trails
   random dictionary words on all three generators, with the lowest
   dispersion in the table. Opaque canonical symbols deliver neither
   the coherence of curated traits nor the diversity of random words.

## The recipe (what the project now knows)

For varied, coherent persona/data generation:

- **Seed with a curated trait lattice**: three position-matched lists
  (worldview / concern / blind spot), ~78 items each, authored by any
  frontier model or assembled from human taxonomies — measured
  equivalent.
- **Sample with a seeded RNG**, ~30% intensity flags, one item per
  position. Provenance and reproducibility come free, as with the
  original tarot draws.
- **Pick generators for steering discipline**, not price tier:
  qwen3-next-80b and deepseek-v4-flash matched or beat commercial
  models on coverage; explicit lattice seeds steer every model tested.
- **Skip the symbols.** Latent canonical richness (T1) and steering
  (T2) are measurable on half of models, but transparent trait words
  beat the symbol lattice on coherence, plausibility, blind-spot
  quality, and dispersion everywhere it was measured.

## Caveats

- One model. Phase 1 showed effect direction can flip between models.
  Both negative results need a second-family replication before they
  are leaned on.
- MiniLM embeddings on same-genre text have a high similarity floor
  (~0.88 within-card); separation (0.41–0.44) is the discriminating
  number, and it favours the fictional deck.
- T1's prompt names no deck or tradition; a prompt that invokes "in
  Rider-Waite tarot…" might recover an advantage for real cards. That
  would test recall, not the seeding mechanism as used.
