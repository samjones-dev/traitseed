# Curated trait lattices: a measured method for diverse, coherent LLM generation

Seed each LLM generation with a draw from a curated trait lattice.
The output is more varied, more coherent and fully reproducible.

We tested this against 5 kinds of baseline, on 18 models, with
decision rules fixed in writing before each run. Curated lattices won on
every quality axis and on diversity at the same time. The supposed
trade-off between varied and coherent output did not appear. It is an
artefact of bad seeds.

## The problem

LLMs collapse when you ask them for variety. Ask for 12 expert
personas and you can get 'Dr Aris Thorne' 9 times, each with the same
even-handed worldview.

These are two separate failure modes, and this method fixes one of
them. Trait lattices fix the worldview collapse: the sameness of
perspective, concern and style. Name repetition is a different
mechanism, and our measurements show semantic seeding barely touches
it. Fix names with explicit name lists or deduplication.

The standard fix is 'be diverse' prompting at high temperature. It
barely helps either failure mode. The variety it buys is sampling
noise: you cannot repeat it and you cannot trace it.

## The method

Seed every generation with a draw from a curated trait lattice:

1. Build 3 position-matched lists: worldview, primary concern and
   blind spot. Each holds about 78 curated items. Any frontier model
   can write one from a short brief. Published psychometric taxonomies
   work equally well.
2. Draw one item per position with a seeded random number generator.
   Mark about 3 in 10 items with an intensity flag, such as 'taken to
   excess'. Each lattice gives about 2 million distinct seeds.
3. Save the draw with each output. Panels become exactly reproducible.
   Every output traces back to its seed.

The blind-spot position matters most. It hands each persona a genuine,
specific flaw. That flaw is what makes synthetic panels disagree
productively instead of converging.

This is the whole method. The rest of this write-up is the evidence.
The evidence is the interesting part, because the method is not where
we started.

## Where the design came from

The project began with a more romantic idea: seed generations with
3-card tarot draws, and let the model's latent knowledge of the
symbolism do the work. That idea contributed the parts the final
method keeps: the 3-position scaffold, the draw entropy and seeded
provenance. It also set the bar, because testing it properly needed
controls strong enough to beat it.

One control was a lattice of plain trait words, matched to the deck's
draw entropy. It won. Everything below is the measurement programme
that established how and why. The symbolic decks serve as the
baselines they turned out to be.

## How we measured

We ran 4 probe families. Each decision rule was written down in the
DESIGN files before its run, with deviations logged. The baselines:

- canonical symbols: tarot, the original idea and the strongest
  symbolic baseline
- an invented deck: tarot's structure with no tradition ('The
  Lantern', 'Nine of Mirrors'), which separates canonical meaning from
  evocative structure
- random words: seeded samples from the system dictionary, which
  separate curation from mere explicitness
- alternative lattices: one written by a different frontier model from
  the same brief, one assembled from human taxonomies (Big-Five
  markers, Rokeach and Schwartz values, named cognitive biases), which
  test authorship effects
- naive diversity prompting: 'make the persona distinctive' at high
  temperature

A judge model from a different family scored 1,260 character studies
blind, for coherence, plausibility and blind-spot quality. We measured
diversity as embedding dispersion, and steering as within-seed against
across-seed variance.

## What the measurements show

**Curated lattices dominate.** On every generator tested, the curated
lattices were at once the most coherent, most plausible, best on
blind-spot quality and most dispersed. There was no trade-off to
manage.

**Curation is the active ingredient.** Random dictionary words bought
high dispersion at the worst coherence scores in the study. Incoherent
'Frankenstein' characters are a real failure mode. Curation is what
avoids it. Naive prompting produced neither diversity nor coherence.

**Authorship is robust.** Lattices from 2 different frontier models
and one built from human taxonomies measured equivalent: within about
0.1 to 0.25 on a 5-point judge scale, in the same dispersion tier.
Writing a lattice is a one-off, automatable step, not a craft
bottleneck.

**Symbols are real but they underperform.** About half the models hold
stable, distinct canonical symbolism, here measured with tarot draws.
On those models the symbols measurably steer generation (9 of 18
overall). Most models expand invented symbols like 'The Hollow Bell'
as fluently and consistently as canonical ones: they are
general-purpose symbol interpreters. But even on the models most
favourable to them, symbol-seeded personas scored below trait-seeded
ones on every quality axis, with less diversity. Routing meaning
through symbols the generator must decode loses information that
plain trait words deliver intact.

**Names are immune to semantic seeding.** Every seed condition left
name collapse largely intact. On one model the surname 'Thorne'
appeared in 21 of 30 personas under both tarot and trait seeds.
Another model produced 'Anya Sharma' 13 of 30 times unseeded. Trait
seeds improved name uniqueness only slightly (from 0.20 to 0.37 unique
full names on the worst model). Each model has a strong name prior
that no semantic seed touches. If you need varied names, add a name
list to the lattice or deduplicate after generation.

**Cheap models are not a compromise.** Open-weight generators
(qwen3-next-80b, deepseek-v4-flash) matched or beat commercial-tier
models on seeded coverage at about a twentieth of the cost. Some
expensive models' apparent diversity is mostly sampling noise. Measure
within-seed variance before trusting one.

## Related work

Conditioning prompts on sampled attributes is established.
[AttrPrompt](https://arxiv.org/abs/2306.15895) showed attributed
prompts beat class-conditional prompts on synthetic-data diversity.
[PersonaHub](https://arxiv.org/abs/2406.20094) scaled
persona-conditioned generation to a billion web-mined personas.
[Persona Generators](https://arxiv.org/abs/2602.03545) evolves
generator code against geometric coverage metrics. Tooling exists
nearby: [EDSL](https://github.com/expectedparrot/edsl) runs surveys
over agents with user-supplied traits, and
[distilabel](https://github.com/argilla-io/distilabel) builds
synthetic-data pipelines. None of these ships the primitive measured
here: a fixed curated lattice with position structure, seeded draws
and per-output provenance.

The closest neighbour is
[Agrawal and Goyal (2026)](https://arxiv.org/abs/2601.18053). They
found that infusing random concepts into prompts increases output
diversity, and they measured only diversity. Our random-words
condition reproduces their gain and adds the axis they left out: the
diversity arrives with the worst coherence scores in the study.
Curation buys both at once. Relatedly,
[fine-grained persona detail does not raise lexical diversity](https://arxiv.org/abs/2505.17390),
which matches our reading: structured sampling, not descriptive
richness, is the active ingredient.

We found no precedent for 4 things: the structure-matched invented
deck that separates canonical meaning from evocative form; judging
coherence and diversity together across symbolic, curated, random and
unseeded conditions; lattice author-robustness; and the blind-spot
position as an engineered, judged disagreement mechanism.

## Limitations

One judge family scored quality. Between 67% and 99% of seeded studies
leak seed vocabulary into prose, so judge blindness is imperfect.
Diversity metrics ride on one small embedding model. The generation
task family is persona and character description; other genres are
untested. Each cell holds 30 to 60 samples.

Single-model conclusions in this domain are unreliable. Two interim
hypotheses flipped as the model grid grew. Every verdict above is a
tally across models, never a single-model headline.

## Use it

The method ships as [traitseed](README.md): the validated lattices
bundled, seeded draws with provenance records, and a one-call lattice
author for domain-tuned lists. The symbolic decks remain available as
research baselines.
