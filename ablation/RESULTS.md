# Ablation results

## Run 1 — google/gemma-4-31b-it:free, seed 42, N=30 per condition

Run 11 June 2026. Artefacts: `runs/gemma-4-31b-it:free-seed42-n30/`.
All 90 calls parsed. Note this is the substitute model (see the run log
in DESIGN.md); the designed `gemini-2.5-flash` run is pending credits.

### Verdict against the pre-registered rule

**The effect does not hold on this model.** The rule required `tarot` to
beat `none` on name uniqueness AND embedding dispersion. Tarot edges name
uniqueness (0.233 vs 0.200 unique full names) but loses embedding
dispersion (0.314 vs 0.333). The unseeded condition produced the most
semantically dispersed panel.

Worse for the thesis: the random-trait control beats tarot on almost
everything it doesn't lose to `none` on.

### Numbers

| metric | none | tarot | traits |
|---|---|---|---|
| unique full names | 0.200 | 0.233 | **0.367** |
| unique first names | 0.133 | 0.200 | **0.233** |
| unique surnames | **0.200** | 0.067 | 0.167 |
| unique institutions | 0.900 | 0.900 | **1.000** |
| distinct-1 | 0.206 | 0.248 | **0.267** |
| distinct-2 | 0.573 | 0.639 | **0.688** |
| mean pairwise Jaccard distance | 0.857 | 0.892 | **0.906** |
| mean pairwise cosine distance | **0.333** | 0.314 | 0.308 |

### What the panels actually look like

Name collapse is total and condition-independent. The model's name prior
dominates any seed:

- `none`: "Aris Thorne" ×15, "Amara Okafor" ×10
- `tarot`: "Alistair Thorne" ×18, surname Thorne ×21 of 30
- `traits`: "Alistair Thorne" ×14, surname Thorne ×21 of 30

This replicates the original consensus observation — tarot alone did not
fix name collapse there either. Names live in a different failure mode
than perspectives: no semantic seed touches them.

### Honest read

1. **Structured seeding lifts lexical diversity** (distinct-n, Jaccard:
   both seeded conditions beat `none`), but plain trait words lift it
   more than tarot cards do.
2. **No seeding helps semantic dispersion** on this model. Both seeded
   conditions slightly compress embedding dispersion relative to `none`.
   A possible mechanism — seeds anchor the persona into a common
   "structured profile" register — is untested speculation.
3. **The tarot-specific claim found no support here.** Nothing in this
   run distinguishes a culturally rich symbol from a random trait word,
   except that the trait word does better.

## Run 2 — google/gemini-2.5-flash, seed 42, N=30 per condition

Run 11 June 2026. Artefacts: `runs/gemini-2.5-flash-seed42-n30/`. This
is the designed model. 13 of 90 responses hit the completion token cap
and lost their closing YAML fence; all were recovered from persisted
raw output by a condition-neutral parser fix (no new API calls). One
recovered record (`none[12]`) has a truncated 4-word perspective; it is
kept — an odd outlier can only inflate `none`'s dispersion, which is
conservative against the seeded conditions.

### Verdict against the pre-registered rule

**Not satisfied, but the failure is narrow.** Tarot beats `none`
decisively on embedding dispersion (0.341 vs 0.237, +44%) and on every
lexical metric, but only ties it on unique full names (0.267 each). The
rule required a win on both.

The trait control again beats tarot on every metric, including
dispersion.

### Numbers

| metric | none | tarot | traits |
|---|---|---|---|
| unique full names | 0.267 | 0.267 | **0.333** |
| unique first names | 0.133 | 0.233 | **0.300** |
| unique surnames | 0.200 | 0.167 | **0.267** |
| unique institutions | 0.933 | 0.867 | **1.000** |
| distinct-1 | 0.192 | 0.220 | **0.241** |
| distinct-2 | 0.603 | 0.678 | **0.730** |
| mean pairwise Jaccard distance | 0.848 | 0.880 | **0.896** |
| mean pairwise cosine distance | 0.237 | 0.341 | **0.368** |

Name collapse persists in every condition, just with gemini's own
favourites: `none` produced "Anya Sharma" ×13 of 30; `tarot` "Elara
Vance" ×10; `traits` spreads widest but still repeats.

## What both runs say together

1. **The tarot-specific claim is unsupported.** On two models, random
   trait words matched or beat tarot cards on every metric. Nothing
   measured here distinguishes a culturally rich symbol system from a
   curated trait list — except the trait list winning.
2. **Positional seeding itself looks real on the stronger model.** On
   gemini, both seeded conditions lift semantic dispersion 44–55% over
   naive diversity prompting and lift all lexical metrics. On gemma the
   dispersion effect reverses, so even this weaker claim is
   model-dependent.
3. **Names are immune to semantic seeding on both models.** Each model
   has a name prior (Thorne/Vance on gemma, Sharma/Vance on gemini)
   that no seed block touches. Name diversity needs a different
   mechanism — explicit constraints, post-hoc dedup, or name lists.

Per the pre-registration: the variance claim as stated is dead. The
honest reframe the data supports is "positional trait seeding improves
panel diversity on capable models; the symbols are optional" — with the
gemma reversal as a caveat. If a write-up happens, that is the story,
and the tarot framing is the hook that did not survive contact with its
own ablation.

## Scope limits (added after review, 11 June 2026)

Everything above is one task (the consensus Delphi persona prompt), one
question, one master seed, N=30 per cell. The task leaves the model
near-total creative freedom, so panel-level variance metrics are noisy
and partly arbitrary. Read the verdicts as: the original task showed no
tarot-specific variance effect — not as evidence about the mechanism.
The mechanism claims (latent symbol richness, seed steering,
human-aligned coherence) are not tested by this design at all; they are
the subject of the phase-2 probes in `probes/DESIGN.md`. The decision
rule here also bundled name uniqueness into the conjunction, which the
data itself shows is governed by a separate mechanism untouched by any
semantic seed — a design flaw in the rule, noted rather than retrofitted.
