---
name: skill-evaluator
description: "Scientifically evaluate a Claude skill's performance — across its input/prompt design, the raw model output it produces, and the output after a review/refinement pass — scored for correctness, quality, efficiency, and consistency. Use this whenever the user wants to evaluate, benchmark, grade, score, audit, or compare a skill (or skill versions), wants to know if a skill's output actually improved after review/refinement, wants statistically defensible before/after numbers, or wants to build out a reusable eval suite for a skill that can grow over time. Complements skill-creator (which drafts/iterates skills) by providing the deeper measurement layer — hypothesis-driven test design, layered scoring (input, raw output, refined output, delta), blind grading, repeated-run statistics, and a pluggable metric registry so new evaluation dimensions can be bolted on later without rewriting the framework. MUST be used, not skill-creator, whenever the question is 'does it actually work / did it get better' — if the request is instead 'write it', 'fix it', or 'improve the wording', that is skill-creator's job, not this one."
---

# Skill Evaluator

A framework for measuring whether a skill actually works — not just once, but reliably, and not just "does it work" but "compared to what, by how much, and how sure are we."

This skill is the measurement layer. `skill-creator` (if available) is the authoring/iteration layer — use it to draft and revise a skill's SKILL.md. Use **this** skill to design the experiment that tells you whether a version, a prompt, or a refinement step actually made things better, in a way that holds up to scrutiny and that you can extend later without starting over.

If `skill-creator` is present in this environment, reuse its infrastructure rather than duplicating it: its `agents/grader.md` (assertion grading), `scripts/aggregate_benchmark.py` (statistical aggregation), and `eval-viewer/generate_review.py` (side-by-side human review) already do solid work for the "raw output, single layer" case. This skill's job is to add the parts that infrastructure doesn't cover: a layered object model, an input/prompt-design layer, a refinement-delta layer, and the scientific scaffolding that keeps the whole thing honest. See `references/skill-creator-integration.md` for exactly how the two fit together.

---

## The core idea: four layers, four axes

Every evaluation question about a skill decomposes into **what you're looking at** (layer) crossed with **what you're measuring** (axis). Keep these separate — conflating them is the most common way evals go wrong (e.g. judging "quality" when you actually mean "did it pass the assertion," or blaming the skill for a bad prompt).

### The four layers (what you're looking at)

| Layer | What it is | Exists for every skill? |
|---|---|---|
| **L0 — Input** | The skill's own definition (SKILL.md: description, instructions, bundled resources) and the test prompts used to exercise it | Always |
| **L1 — Raw output** | What the model produces on its first pass through the skill, given an L0 prompt | Always |
| **L2 — Refined output** | What the model produces after a review/refinement step (human feedback, a self-critique pass, an iteration loop) is applied to L1 | Only if the skill/workflow actually has a refinement step |
| **L3 — Delta** | Not measured directly — computed as the difference between L2 and L1 | Only if L2 exists |

Read `references/layers-and-metrics.md` before designing any eval — it defines exactly what "good" looks like at each layer and gives worked examples.

### The four axes (what you're measuring)

| Axis | Nature | How it's scored |
|---|---|---|
| **Correctness** | Objective, binary | Pre-registered assertions, checked against the output (reuse skill-creator's `grader.md` pattern) |
| **Quality** | Subjective, graded | Rubric score (1–5 per dimension) from a blind judge — for things assertions can't capture (tone, design taste, judgment calls) |
| **Efficiency** | Objective, continuous | Tokens, tool calls, wall-clock time, cost proxy |
| **Consistency** | Statistical, derived | Variance across N≥3 repeated runs of the *same* prompt+skill+layer combination — mean ± stddev, never a single sample |

Not every axis applies to every layer with equal force (L0 has no "efficiency" in the token sense — see the reference doc), but the crossing is the mental model to hold onto: before scoring anything, know which cell of the layer × axis grid you're in.

---

## Non-Negotiables

The full reasoning for each of these lives in the reference docs — collected here so they're scannable in one pass before you run anything, the same way `agents/input-layer-judge.md` keeps its own "Non-Negotiables When Evaluating" list for the rubric it hands out.

- **Never invent a synthetic L2 refinement step just to have one to score.** If the skill has no real review/feedback loop, skip L2/L3 and say so (`references/layers-and-metrics.md`).
- **Never write assertions after seeing output.** Pre-register them in Step 1, before any run — assertions written post-hoc unconsciously fit what already happened (`references/scientific-method.md` #1).
- **Never report a number without its control.** "85% correctness" compared to what? State the baseline, or say explicitly that you skipped it (`references/scientific-method.md` #2).
- **Never treat N=1 as a consistency claim.** N≥3 is the floor for a stddev to mean anything (`references/scientific-method.md` #3).
- **Never let a quality judge see which configuration produced an output before scoring it.** Blind A/B, reveal the mapping only after scores are recorded (`references/scientific-method.md` #4).
- **Never round an ambiguous assertion up to a pass (or down to a fail).** Mark it `null`, quote the ambiguity, and flag it for the next L0 pass (`agents/grader.md` #4).
- **Never edit an assertion mid-grade**, even to fix wording you now see is bad — note the problem, grade it as written (`agents/grader.md` #5).
- **Never collapse "did it get better" and "was it worth it" into one verdict.** A correctness gain that costs 4x the tokens is a trade-off to report, not an automatic win (`references/scientific-method.md` #5).
- **Never write a surprising result straight into the report.** Re-run first — distinguish a real effect from a fluky run or a grading bug (`references/scientific-method.md` #7).

---

## Workflow

### Step 0: Scope the evaluation

Ask (or infer from context):
1. Which skill, which version(s)? (Single skill audit vs. A/B comparison vs. before/after a refinement step — for A/B comparison specifically, see `agents/comparator.md`)
2. Does this skill/workflow have a real L2 (refinement) step, or only L1? Don't manufacture a refinement layer that doesn't exist in practice — if there's no review/feedback loop in how the skill is actually used, skip L2/L3 entirely and say so.
3. Which axes matter most for this skill? A pure data-transform skill lives and dies on correctness; a writing-style skill lives and dies on quality; a frequently-invoked skill cares a lot about efficiency and consistency.
4. Is skill-creator's infrastructure available in this environment? (Check for `/mnt/skills/*/skill-creator/`.) If yes, plan to reuse it per `references/skill-creator-integration.md`. If no, this skill's own `scripts/` provide fallbacks.

**Do NOT load** `references/skill-creator-integration.md`'s reuse table if skill-creator isn't present — jump straight to that file's "When skill-creator isn't available" section instead; the table above it describes infrastructure you won't be touching.

State this scope back to the user in a sentence or two before building anything — it's cheap to correct now and expensive to redo later.

**L0-only fast path:** If the request asks only for an input-layer report, set `scope.layers` to `["L0"]`, set `has_refinement_step` to `false`, omit L1/L2/L3 and baseline work, and exclude any unrequested axes. Read only `SKILL.md`, `agents/input-layer-judge.md`, `references/schemas.md`, and the prepared `evals/eval_plan.json` prompt; write `l0_scores.json` and its Markdown rendering. Do not create L1 assertions or run-output records.

### Step 1: Pre-register the hypothesis and assertions

Before running anything:
- Write down what you expect to see and why ("v2's more explicit error-handling instructions should raise correctness on malformed-input test cases without adding much token overhead").
- Write correctness assertions for L1 (and L2, if it exists) *before* looking at any actual output. This is the single most important scientific-hygiene step in this whole skill — assertions written after seeing outputs tend to unconsciously fit what already happened, which defeats the point of having them.
- Decide N (repeats per test case) up front. N=1 tells you nothing about consistency. N=3 is a reasonable default; go higher (5–10) for anything with high stakes or known flakiness.
- Log all of this in `evals/eval_plan.json` — see `references/schemas.md` for the shape. This is what makes the eval reproducible and extensible: six months from now, someone (including you) should be able to read this file and know exactly what was being tested and why.

The pre-registration and control rationale is documented in `references/scientific-method.md`; keep the plan explicit even when a requested scope omits L1 or later layers.

### Step 2: Run L0 — score the input layer

*Axes in play: correctness and quality only — L0 has no per-run efficiency or consistency score (see the grid above; there's no "run" to time or repeat at this layer).*

Before spending compute on L1/L2 runs, sanity-check the input itself. A skill can fail purely because its description undertriggers, or its instructions are ambiguous; the scientific-method rationale for this gate is in `references/scientific-method.md`.

Use `agents/input-layer-judge.md`, which scores two separate artifacts:
- **The full 8-dimension, 1–5-per-dimension skill-quality rubric (D1–D8, 40 points max)** — score all eight, not just D4. D4 (Description Quality) is the one most directly about triggering: would this description fire reliably on realistic queries, including near-miss negatives? (If skill-creator is present, its "Description Optimization" trigger-eval loop is the more rigorous version of that D4 check specifically — defer to it when available.)
- **Instruction clarity** and **test prompt realism** (the file's separate "Eval-Design Checks" section, 1–5 each): are steps unambiguous enough that two independent runs would take the same approach, and are the L1 test prompts things a real user would actually type, including messy/casual phrasing?

Record scores in `evals/l0_scores.json` (`dimensions` + `eval_design_checks`, per `references/schemas.md`).

**Checkpoint — stop here if L0 is weak.** If `dimensions.total_score` is a clear fail (D grade or below) or any `eval_design_checks` score is ≤2, don't proceed into Step 3. Flag the specific gap to the user and get a decision: fix it now, or proceed anyway with the gap noted as a caveat on every L1/L2 result that follows. Running an N-repeat L1 batch against instructions or prompts already known to be weak just measures noise at N× the cost — the same reasoning as Step 0's checkpoint, applied to the layer this skill exists to catch cheaply.

### Step 3: Run L1 — raw output

*Axes in play: all four — correctness, quality, efficiency, and consistency (consistency only resolves once N≥3 repeats are in; a single run gives you a point estimate, not a consistency score).*

For each test prompt, run N repeats with the skill active (and, where relevant, N baseline repeats without the skill / with the prior version — see `references/layers-and-metrics.md` for when a baseline is worth the cost).

Grade each run's correctness against the pre-registered assertions. Use skill-creator's `agents/grader.md` when reachable; otherwise use this skill's `agents/grader.md`. **Do NOT load both.** For quality, use this ordered fallback: (1) `agents/manual-tc-quality-judge.md` when the skill writes manual test cases, (2) skill-creator's quality-rubric judge when reachable for another skill type, or (3) write and preregister a lightweight rubric in `eval_plan.json` from the concerns named in Step 0.3. **`agents/input-layer-judge.md` is L0-only** and must not grade L1/L2 output. Capture tokens/time/tool-calls per run.

Save per-run results in `<workspace>/L1/<eval-id>/run-<n>/` following `references/schemas.md`.

**If Step 0 scoped this as an A/B comparison** (two skill versions, or with_skill vs. without_skill): do not grade each configuration independently with its label visible, the way the paragraph above describes — that defeats the blinding `references/scientific-method.md` rule 4 requires. Instead, feed both configurations' raw outputs to `agents/comparator.md`, labeled only "A" and "B"; it performs its own blind grading pass and returns the comparison directly (registered as `version_ab_delta` in `metrics_registry.json`). Its output doesn't fit the per-configuration `result.json` shape in `references/schemas.md` — save it separately (e.g. `<workspace>/L1/<eval-id>/ab-comparison.json`) and carry it into Step 6's report as its own section, the same way L3's delta sits alongside L1/L2 rather than inside them. `scripts/aggregate_layered.py` does not currently parse this shape — aggregate A/B comparisons across repeats by hand until that's extended.

### Step 4: Run L2 — refined output (only if it exists)

*Axes in play: the same four as L1, scored with the same assertions and rubric — that's what makes an L1→L2 comparison meaningful rather than two unrelated numbers.*

**Do NOT load `agents/refinement-analyzer.md`, or read the L2/L3 rows of the layer × axis grid above, if Step 0 found no real refinement step** — skip straight to Step 6 and report L1 only; a synthetic L2 built just to have something to load here violates the Non-Negotiables above.

Feed each L1 output through the actual refinement mechanism the skill/workflow uses (human feedback + re-run, a self-review pass, an editor step — whatever is real, not a synthetic one invented for the eval). Grade L2 exactly as L1 was graded, using the *same* assertions and rubric so scores are comparable.

### Step 5: Compute L3 — the delta

*Axes in play: correctness, quality, and efficiency, all derived (L2 minus L1) — not consistency, since the delta of a spread isn't meaningful the same way a delta of a mean is.*

Use `agents/refinement-analyzer.md` to answer, per test case and in aggregate:
- Did correctness improve from L1 → L2? By how much?
- Did quality improve? Where specifically (cite what changed)?
- What did the refinement *cost* (extra tokens/time)? Was the gain worth it?
- Did refinement fix real problems, or just churn wording without changing substance? (This distinction matters — a refinement step that burns tokens without moving the correctness/quality needle is a target for removal, not celebration.)

This is the piece most eval setups skip, and it's usually where the most actionable insight lives — it tells you whether your *review process*, not just your skill, is pulling its weight.

### Step 6: Aggregate and report

Aggregate into a layer-tagged benchmark file (`references/schemas.md` extends skill-creator's `benchmark.json` with a `layer` field, so its existing viewer/aggregator can be reused with a small adapter — see `scripts/aggregate_layered.py`). Report, per layer:
- Correctness: pass rate, mean ± stddev across N
- Quality: mean rubric score ± stddev
- Efficiency: mean tokens/time ± stddev
- Consistency: stddev itself, called out explicitly — high variance is a finding, not noise to average away

If skill-creator's `eval-viewer` is available, reuse it (it already renders prompt/output/grades/feedback side by side and reads the same field names this skill writes). Otherwise present results directly in conversation, one test case at a time.

### Step 7: Iterate, and grow the registry

Fix what the numbers point to, re-run, compare against the pre-registered hypothesis (did it hold?). Any new metric you found yourself wanting mid-evaluation — add it to `references/metrics_registry.json` rather than hard-coding it into a one-off script, so the next evaluation (of this skill or any other) can pick it up. See "Extending this framework" below.

---

## Extending this framework

The framework is deliberately built around one seam: **the metric registry** (`references/metrics_registry.json`). Each entry declares:
- `name` and `axis` (correctness / quality / efficiency / consistency)
- `applies_to_layers`: which of L0/L1/L2/L3 it's meaningful for
- `scorer_type`: `assertion` (script-checkable), `rubric` (needs a blind judge), or `derived` (computed from other metrics, e.g. anything in L3)
- a pointer to the scoring logic (a script in `scripts/`, or a prompt in `agents/`)

To add a new evaluation dimension later (say, "hallucination rate" or "style consistency with a brand guide"): write the scorer, add one registry entry, done — the workflow steps above don't change. This is what makes the framework extensible to skills this design didn't anticipate: the four-layer/four-axis grid stays fixed, only the registry grows.

To extend to a *general-purpose* evaluator for arbitrary skills (not just the one you're starting with): the only skill-specific parts of this whole framework are (a) the test prompts, (b) the assertions, and (c) whether L2 exists. Everything else — the layer model, the axes, the statistical treatment, the registry mechanism — is already skill-agnostic. Generalizing later mainly means templating Step 0's scoping questions rather than restructuring anything.

## Reference files

- `references/layers-and-metrics.md` — full definition of the four-layer object model with worked examples, and guidance on which axes apply to which layers
- `references/scientific-method.md` — the methodology rules (pre-registration, blinding, controls, sample size) in more depth, with rationale
- `references/schemas.md` — JSON schemas for `eval_plan.json`, `l0_scores.json`, layer-tagged run/benchmark files, and `metrics_registry.json`
- `references/skill-creator-integration.md` — exactly which skill-creator files to reuse vs. what this skill adds. **Do NOT load** the reuse table if skill-creator is absent — its own "When skill-creator isn't available" section is the only part that applies then.
- `agents/input-layer-judge.md` — rubric and instructions for scoring L0 (description/instructions/prompt quality)
- `agents/grader.md` — fallback assertion grader for L1/L2 correctness, used when skill-creator's `agents/grader.md` isn't available. **Do NOT load** this if skill-creator's own `grader.md` is reachable.
- `agents/manual-tc-quality-judge.md` — rubric-based quality judge for skills that write manual test cases (registered as `manual_tc_quality_score` in `metrics_registry.json`). **Do NOT load** this for any skill that isn't a test-case writer.
- `agents/refinement-analyzer.md` — instructions for computing the L1→L2 delta. **Do NOT load** if Step 0 found no real refinement step — there's no L2 to delta against.
- `agents/comparator.md` — blind A/B fallback for comparing two skill *versions'* outputs at the same layer (registered as `version_ab_delta` in `metrics_registry.json`); distinct from `refinement-analyzer.md`, which compares L1 vs L2 within one version. **Do NOT load** this if skill-creator's own `agents/comparator.md` + `agents/analyzer.md` are reachable, or if Step 0 isn't doing an A/B comparison at all.
- `scripts/aggregate_layered.py` — aggregates layer-tagged run data into statistics (mean/stddev/delta per layer × axis)
