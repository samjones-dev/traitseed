# Ablation design

Written before any generation run. The decision rule is fixed here so the
results cannot move it.

## Claim under test

Seeding persona generation with a 3-card tarot spread produces more diverse
panels than (a) asking for diversity with no seed and (b) seeding with random
trait words. "Diverse" means: higher embedding dispersion, higher lexical
diversity, fewer name and institution collisions.

The claim is unvalidated. The consensus pipeline that produced the original
impression also used a banned-name list, used-name tracking, example names,
and dedup retries. Tarot alone did not fix name collapse there.

## Single variable

The seed block in the persona prompt. Nothing else differs between
conditions.

| Condition | Seed block |
|---|---|
| `tarot` | 3-card spread, positions: worldview, concern, blind spot |
| `none` | "Make the persona distinctive and diverse." — naive diversity instruction |
| `traits` | 3 random traits from position-matched 78-item lists |

## Held constant across conditions

- Prompt scaffold: identical apart from the seed block.
- Sampling: temperature 1.2, top_p 0.95 (the consensus persona settings).
- Model: `google/gemini-2.5-flash` via OpenRouter (the consensus default).
- Independence: every call is a fresh context. No used-name tracking, no
  banned names, no example names, no dedup retries. We measure raw collapse.
- N = 30 personas per condition, same question
  (`ai_education_q1` from consensus).
- RNG: one master seed; draws and trait picks persisted per persona.

## Confounds stripped from the consensus prompt

- Banned-name list ("Amara Okonkwo" etc.)
- Used-names tracking across the panel
- The 15 example "diverse names"
- Explicit instructions to vary culture, gender, institution type, career
  stage — these are diversity interventions in their own right
- Dedup retry loop

## The traits control

The control is deliberately strong, not a strawman. Three hand-curated
78-item lists, one per spread position (disposition, concern, blind spot).
Entropy is matched to the tarot draw:

- Tarot: log2(78 × 77 × 76) ≈ 18.8 bits + 3 reversal flags at p=0.3
  (≈ 2.6 bits) ≈ 21.4 bits.
- Traits: log2(78³) ≈ 18.8 bits + 3 intensity flags at p=0.3 ≈ 21.5 bits.

The intensity flag mirrors reversal: with p=0.3 a trait is marked as its
distorted form ("taken to excess", "to the point of obsession", "severe").

If tarot beats this control, the symbol lattice adds something beyond
structured random conditioning. If it only beats `none`, the finding is
"positional seeding works", not "tarot works".

## Metrics

Computed per condition over the 30 personas:

1. **Name uniqueness** — unique full names / 30; also unique first names
   and surnames separately. Same for institutions (exact, case-folded).
2. **Lexical diversity** — distinct-1 and distinct-2 over the concatenated
   `persona` + `perspective` texts; mean pairwise Jaccard distance over
   content words.
3. **Embedding dispersion** — mean pairwise cosine distance of
   `perspective` texts (sentence-transformers, all-MiniLM-L6-v2, local).

## Decision rule (pre-registered)

- **Effect holds** if `tarot` beats `none` on name uniqueness AND embedding
  dispersion, with lexical diversity not worse.
- The `tarot` vs `traits` comparison is reported either way. Tarot winning
  it is the publishable contribution; losing it reframes the write-up as
  "structured seeding works, symbols optional".
- If `tarot` does not beat `none`, the variance claim is dead and the
  write-up does not happen. Say so in RESULTS.md.

## Run log and deviations

- **11 June 2026** — OpenRouter credits exhausted ($1660.05 used of
  $1660). Run 1 executes on `google/gemma-4-31b-it:free` instead of
  `google/gemini-2.5-flash`. The model is still constant across the three
  conditions, so the within-run comparison stands; what changes is
  continuity with the consensus pipeline. Re-run on gemini-2.5-flash when
  credits return — a second model doubles as a cross-model check, which
  strengthens the write-up either way.

## Costs and provenance

About 90 LLM calls, ~$0.20. Every run persists: master seed, per-persona
seed material (cards or traits), raw model output, parsed fields, model id,
sampling params. Artefacts are committed.
