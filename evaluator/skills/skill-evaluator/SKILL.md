---
name: skill-evaluator
description: "Scientifically evaluate a Claude skill's performance — across its input/prompt design, the raw model output it produces, and the output after a review/refinement pass — scored for correctness, quality, efficiency, and consistency. Use this whenever the user wants to evaluate, benchmark, grade, score, audit, or compare a skill (or skill versions), wants to know if a skill's output actually improved after review/refinement, wants statistically defensible before/after numbers, or wants to build out a reusable eval suite for a skill that can grow over time. Complements skill-creator (which drafts/iterates skills) by providing the deeper measurement layer — hypothesis-driven test design, layered scoring (input, raw output, refined output, delta), blind grading, repeated-run statistics, and a pluggable metric registry so new evaluation dimensions can be bolted on later without rewriting the framework."
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

## Workflow

### Step 0: Scope the evaluation

Ask (or infer from context):
1. Which skill, which version(s)? (Single skill audit vs. A/B comparison vs. before/after a refinement step)
2. Does this skill/workflow have a real L2 (refinement) step, or only L1? Don't manufacture a refinement layer that doesn't exist in practice — if there's no review/feedback loop in how the skill is actually used, skip L2/L3 entirely and say so.
3. Which axes matter most for this skill? A pure data-transform skill lives and dies on correctness; a writing-style skill lives and dies on quality; a frequently-invoked skill cares a lot about efficiency and consistency.
4. Is skill-creator's infrastructure available in this environment? (Check for `/mnt/skills/*/skill-creator/`.) If yes, plan to reuse it per `references/skill-creator-integration.md`. If no, this skill's own `scripts/` provide fallbacks.

State this scope back to the user in a sentence or two before building anything — it's cheap to correct now and expensive to redo later.

### Step 1: Pre-register the hypothesis and assertions

Before running anything:
- Write down what you expect to see and why ("v2's more explicit error-handling instructions should raise correctness on malformed-input test cases without adding much token overhead").
- Write correctness assertions for L1 (and L2, if it exists) *before* looking at any actual output. This is the single most important scientific-hygiene step in this whole skill — assertions written after seeing outputs tend to unconsciously fit what already happened, which defeats the point of having them.
- Decide N (repeats per test case) up front. N=1 tells you nothing about consistency. N=3 is a reasonable default; go higher (5–10) for anything with high stakes or known flakiness.
- Log all of this in `evals/eval_plan.json` — see `references/schemas.md` for the shape. This is what makes the eval reproducible and extensible: six months from now, someone (including you) should be able to read this file and know exactly what was being tested and why.

### Step 2: Run L0 — score the input layer

Before spending compute on L1/L2 runs, sanity-check the input itself. A skill can fail purely because its description undertriggers, or its instructions are ambiguous — no amount of L1/L2 evaluation fixes that; you'd just be measuring noise.

Use `agents/input-layer-judge.md` to score:
- **Description quality**: would this description trigger reliably on realistic queries, including near-miss negatives? (If skill-creator is present, its "Description Optimization" trigger-eval loop is the more rigorous version of this — defer to it when available.)
- **Instruction clarity**: are steps unambiguous enough that two independent runs would take the same approach?
- **Test prompt realism**: are the L1 test prompts things a real user would actually type, including messy/casual phrasing?

Record scores in `evals/l0_scores.json`. Low L0 scores are worth fixing before running expensive L1/L2 batches.

### Step 3: Run L1 — raw output

For each test prompt, run N repeats with the skill active (and, where relevant, N baseline repeats without the skill / with the prior version — see `references/layers-and-metrics.md` for when a baseline is worth the cost).

Grade each run's correctness against the pre-registered assertions (adapt skill-creator's `agents/grader.md` if present, or use this skill's fallback in `agents/`). Score quality via blind rubric judging where correctness alone doesn't capture it. Capture tokens/time/tool-calls per run.

Save per-run results in `<workspace>/L1/<eval-id>/run-<n>/` following `references/schemas.md`.

### Step 4: Run L2 — refined output (only if it exists)

Feed each L1 output through the actual refinement mechanism the skill/workflow uses (human feedback + re-run, a self-review pass, an editor step — whatever is real, not a synthetic one invented for the eval). Grade L2 exactly as L1 was graded, using the *same* assertions and rubric so scores are comparable.

### Step 5: Compute L3 — the delta

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
- `references/skill-creator-integration.md` — exactly which skill-creator files to reuse vs. what this skill adds
- `agents/input-layer-judge.md` — rubric and instructions for scoring L0 (description/instructions/prompt quality)
- `agents/refinement-analyzer.md` — instructions for computing the L1→L2 delta
- `scripts/aggregate_layered.py` — aggregates layer-tagged run data into statistics (mean/stddev/delta per layer × axis)
