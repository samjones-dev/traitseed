# Phase-2 mechanism probes

Written before any generation. These test the mechanism the phase-1
ablation never touched: that tarot card names index dense meta-patterns
in the model's human-generated training data, and that this latent
depth — not just positional structure — does useful work.

Phase 1 (ablation/) tested panel variance on one inherited task and is
weak evidence either way; see the scope limits in ablation/RESULTS.md.

## The fictional-deck control

The sharp foil for the mechanism claim is an invented deck with the
same structure and draw entropy but no canonical interpretive
tradition: 22 invented majors ("The Lantern", "The Cartographer") plus
4 invented suits × the same 14 ranks. Reversals identical.

Two acknowledged residuals it cannot ablate:

- Invented names still connote (any evocative phrase does). What is
  ablated is the dense, documented, canonical symbol system.
- Ranks and numbers keep their numerological priors. Suit and major
  semantics are the ablated part.

## T1 — symbol expansion probe

**Claim (latent richness):** card names alone activate stable, dense,
mutually distinct symbolism the model already knows.

**Design:** for every card in both decks (78 + 78, upright only), ask
the model k=8 times: what worldview or disposition does this card
connote, in 2–3 sentences. Identical prompt for both decks.
Temperature 1.0, top_p 0.95, model `google/gemini-2.5-flash`.
1248 calls, ≈ $0.50.

**Metrics** (embeddings: all-MiniLM-L6-v2, local):

- *Stability*: per card, mean pairwise cosine similarity across its 8
  expansions; deck score = mean over cards.
- *Separation*: deck mean of (within-card similarity − mean similarity
  of that card's expansions to all other cards' expansions). Stable AND
  distinct is the claim; stable-but-identical (one blob) fails it.

**Decision rule (pre-registered):** latent richness holds if the real
deck beats the fictional deck on BOTH stability and separation. Report
per-card distributions and the major/minor split either way.

## T2 — fixed-seed steering probe

**Claim (steering):** a draw systematically shapes generation — the
same seed pulls repeated generations in a consistent direction, and
real symbols steer more than structure alone.

**Design:** three conditions — `tarot`, `fictional`, `traits` — each
with m=10 distinct draws, k=6 replicate generations per draw.
Identical positional scaffold (worldview / concern / blind spot). The
task is a free-standing character study (150–250 words, plain text),
NOT the consensus Delphi persona task. Same sampling as phase 1
(temperature 1.2, top_p 0.95) because steering under high temperature
is the regime the method targets. 180 calls, ≈ $0.20.

**Metric:** steering ratio = mean pairwise cosine distance across
draws ÷ mean pairwise cosine distance within draws. Higher = the seed,
not sampling noise, determines where the output lands. Within-draw and
across-draw components reported separately (consistency vs coverage).

**Decision rule (pre-registered):** steering-via-latent-depth holds if
tarot's steering ratio exceeds the fictional deck's. Tarot vs traits is
reported either way: tarot winning it would recover the phase-1 loss;
losing it says curated trait words steer at least as well as symbols.

## Battery backlog

Sketches only. Each gets a full pre-registration (rule fixed, signed
off) before any generation. T1/T2 results steer which run next.

### T3 — synthetic survey panel (designed, deferred)

Human-alignment made literal: seeded respondents answer opinion
questions that have published human response distributions (Pew or
Gallup toplines, verified before the run, options matching the survey
instrument). Conditions: tarot, fictional, traits, none. Metrics:
Jensen–Shannon distance from panel marginals to human marginals;
distribution entropy. The strong claim: seeded panels approximate human
opinion spread better than naive prompting, without degenerating into
uniform noise. Memorisation of toplines is the known confound — the
`none` condition is the control for it.

### T4 — coherence × diversity Pareto (pre-registered 11 June 2026)

Sam's original objection made measurable: dispersion alone rewards
incoherent scatter. Claim: tarot sits on the Pareto frontier —
trait-level dispersion is bought with Frankenstein combinations;
symbol-seeded characters cohere.

**Generators:** the three models where both T1 and T2 rules held —
`qwen3-next-80b`, `kimi-k2-0905`, `gemini-3.1-pro-preview`.

**Data:** T2 artefacts reused (60 studies per condition per model)
plus a fresh `none` cell per model: 60 studies, identical prompt with
the seed block replaced by "Make the person distinctive.", same
sampling as that model's T2 run.

**Judge:** `claude-sonnet-4.6` — different family from all three
generators. Temperature 0. Sees only the study text, never the seed.
Scores 1–5 on five dimensions: coherence (one psychologically
consistent person vs contradictory fragments), plausibility (a real,
specific human vs generic or impossible), and three blind-spot
dimensions shared with T6. JSON output, two parse retries.

**Metrics:** per model × condition — mean(coherence, plausibility);
dispersion = mean pairwise cosine distance over all 60 studies
(computed identically for all four conditions, ignoring draw
structure). Leakage spot-check: fraction of seeded studies whose text
contains a token from their own seed; reported alongside.

**Decision rule:** T4 holds on a model if tarot
mean(coherence + plausibility) > traits. Tarot vs fictional and vs
none reported either way. Verdicts stated per-model with a tally,
never as a single headline.

### T6 — blind-spot productivity (pre-registered 11 June 2026)

The spread's third position claims to inject genuine flaws. The T2
scaffold asks every condition for a blind spot; the seed is what
differs. Judged on the same pass as T4.

**Metrics:** per model × condition — mean of blind-spot genuineness
(real flaw vs flattering pseudo-flaw), specificity (concrete and
behavioural vs vague), integration (connected to the character's
strengths vs bolted on). Secondary contrast: studies seeded with at
least one reversed card vs none, within tarot and fictional
conditions.

**Decision rule:** T6 holds on a model if tarot mean blind-spot score
(three dimensions averaged) > none. Tarot vs traits is reported either
way — traits get the flaw handed to them verbatim, so specificity
should favour traits; integration is the interesting dimension.
Reversal contrast is reported, not gated.

### T5 — symbol compositionality (new)

T1's sharpest internal contrast: fictional majors were the most
distinct symbols measured ("The Empty Chair" 0.60) while abstract-suit
minors were the weakest ("Ten of Keys" 0.22). Probe what makes a name
expand well: generate candidate symbol names varying concreteness,
modifier evocativeness, and structure (article-noun, rank-of-suit,
compound), measure T1-style stability and separation per feature.
Output is not a verdict but design rules for deck generation — the
feature the inverted thesis needs.

### T7 — position attribution (new)

Do all three spread positions shape the output, or does one dominate?
For fixed draws, regenerate with one position ablated (replaced by a
neutral filler) at a time; measure embedding shift per position.
Tests whether the spread is a working scaffold or decoration around a
single dominant seed.

### T8 — downstream panel disagreement (new)

The application endpoint: full panels (one per condition) respond to a
contested question; measure stance spread and argument-type coverage
across the panel. This is the consensus use case run as an experiment
rather than inherited as one.

### T7L — lattice controls (pre-registered 11 June 2026)

The T4/T6 winner ("traits") is a Claude-authored lattice, so the result
is "frontier-model-distilled trait lattice beats canonical symbols",
not "any words beat symbols". Project goal is now method-first: find
the best seed lattice for varied, coherent generation. Three controls
isolate what makes the trait lattice win:

| condition | lists | isolates |
|---|---|---|
| `degraded` | seeded random words from /usr/share/dict/words | explicitness without curation |
| `lattice2` | same authoring brief, executed by gpt-4.1 | author-dependence |
| `human` | Goldberg Big-Five markers; Rokeach/Schwartz values + SDG themes; named cognitive biases | human vs LLM curation |

All lattices: three 78-item position lists, persisted as JSON under
probes/lattices/ and committed before generation; same positional
scaffold, intensity flags, and draw entropy as `traits`. Generation:
T2 protocol (10 draws x 6 reps) on qwen3-next, kimi-k2,
gemini-3.1-pro. Judging: same blind sonnet-4.6 pass as T4/T6.
Comparators: existing `traits` and `none` rows (same generators,
prompt, judge).

**Decision rules:**
- R1 (curation matters): `degraded` < `traits` on T4 score per
  generator. If degraded ≈ traits, any explicit words work and
  curation is irrelevant.
- R2 (author-robust): `lattice2` > `none` on T4 score per generator.
  The traits−lattice2 gap is reported, not gated.
- R3: `human` reported on the same axes, no gate.
- Primary output: per-generator ranking of all six conditions on the
  T4 x dispersion plane.

Known caveats, accepted: human-list transcription is LLM-mediated
(curation is human, recall is mine); degraded lists from the system
dictionary skew archaic — that is what zero curation means.

## Replication note

Both probes run on one model first. Before any write-up, the surviving
claims re-run on a second model family (budget permits). One-model
results are treated as provisional — phase 1's gemma/gemini dispersion
reversal is the cautionary tale.

**Replication set (11 June 2026):** both T1 rules failed on gemini, so
the negative results replicate rather than the survivors — a failure
that holds across families is a finding; one that flips is phase 1
again. Models: `openai/gpt-4.1-mini`, `anthropic/claude-haiku-4.5`,
`qwen/qwen3-next-80b-a3b-instruct`. Same seeds, same draws. One
deviation: Anthropic caps temperature at 1.0, so the Claude T2 run uses
1.0 instead of 1.2 (recorded in its manifest); cross-condition ratios
within a model remain comparable, cross-model absolute values were
never comparable anyway.

## Provenance

As phase 1: master seed 42, per-slot derived RNGs, JSONL records with
raw output and seed material, manifest at run start, streaming writes.
