---
name: skill-evaluator
description: "Scientifically evaluate a Claude skill — layered L0-L3 scoring, blind grading, repeated-run stats, an extensible metric registry. Use to: (1) evaluate, benchmark, grade, or audit a skill; (2) compare two skills or versions, including blind A/B; (3) check if refinement improved output and was worth its cost; (4) build a reusable eval suite. MUST use this, not skill-creator, for 'does it work / did it improve' — use skill-creator for 'write it' or 'fix it'."
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

These are the rules that are specific to *this* framework's mechanics — not general scientific-method advice (that's the shorter list right after, and lives in full in `references/scientific-method.md`), but the procedural teeth unique to evaluating a layered, multi-axis skill:

- **Never invent a synthetic L2 refinement step just to have one to score.** A made-up refinement step measures the model reviewing its own work once, not the skill's actual review process — that's a different, weaker claim wearing the same L2 label. If the skill has no real review/feedback loop, skip L2/L3 and say so (`references/layers-and-metrics.md`).
- **Never round an ambiguous assertion up to a pass (or down to a fail).** Resolving the ambiguity yourself hides an L0 problem (an under-specified assertion) behind what looks like a clean L1 result — mark it `null`, quote the ambiguity, and flag it for the next L0 pass (`agents/grader.md` #4).
- **Never edit an assertion mid-grade**, even to fix wording you now see is bad. Changing the target after seeing the output is the same pre-registration violation as writing it post-hoc in the first place — note the problem, grade it as written (`agents/grader.md` #5).
- **Never collapse "did it get better" and "was it worth it" into one verdict.** A correctness gain that costs 4x the tokens is a trade-off to report, not an automatic win — the two are different axes (`agents/refinement-analyzer.md`'s substance-vs-polish call) that can move independently, and folding them into one number hides exactly the trade-off a reader needs to see.
- **Never let `compute_l3_delta` (or any aggregation step) pick a `configuration` silently.** Zero shared configs between L1 and L2 gets reported as an explicit gap — not a quietly-empty `{}` that looks like "nothing to report" instead of "something went unmeasured." When *multiple* shared configs exist, the script doesn't gap out (a real delta is still computable and worth having) — it auto-resolves deterministically (`with_skill` if present, else the first sorted candidate) and names the untaken alternatives in `other_shared_configs_not_deltad`, so the choice is visible rather than assumed (`scripts/aggregate_layered.py`).
- **Never let a scoring rubric's own file contain a pre-written verdict about itself.** This one is scar tissue, not theory: an earlier version of `agents/input-layer-judge.md` carried a "Self-Evaluation Note" that pre-wrote a favorable justification for each of the 8 dimensions, sitting in the exact file every grader must load to get the rubric — so every self-evaluation of this framework silently read the "intended" answer before scoring a single dimension. It took several independent blind-graded rounds before anyone noticed the scores were suspiciously self-congratulatory and traced it back to that note. It's gone now, and won't come back in a rubric file — verdicts about a Skill's quality belong in a grading pass's own output (`l0_scores.json`), never pre-loaded into the instrument doing the grading.

**Also assumed** (standard comparative-experiment hygiene this framework doesn't reinvent, just enforces mechanically — full reasoning in `references/scientific-method.md`): pre-register hypotheses/assertions before any run (#1); always report a number against its control (#2); N≥3 before claiming consistency (#3); blind the grader on subjective quality axes (#4); keep pre-registered findings and exploratory observations in separate sections of the report, never merged (#6 — mechanically, this means `evals[].exploratory_assertions[]` per `references/schemas.md` never feeds `correctness.pass_rate`, and Step 6 reports them in their own subsection); re-run before trusting a surprising result (#7).

---

## Workflow

### Step 0: Scope the evaluation

Ask (or infer from context):
1. Which skill, which version(s)? (Single skill audit vs. A/B comparison vs. before/after a refinement step — for A/B comparison specifically, see `agents/comparator.md`)
2. Does this skill/workflow have a real L2 (refinement) step, or only L1? Don't manufacture a refinement layer that doesn't exist in practice — if there's no review/feedback loop in how the skill is actually used, skip L2/L3 entirely and say so.
3. Which axes matter most for this skill? Resolve by what the skill's primary failure mode is, not by guessing:

   | If the skill's output is... | Primary axis | Why |
   |---|---|---|
   | Structured/checkable (data extraction, code, file transforms) | Correctness | A wrong answer is wrong regardless of how it's phrased — assertions catch this directly. |
   | Judged by taste/tone/clarity (prose, design, explanations) | Quality | No assertion can check "is this well-written" — needs the blind rubric axis. |
   | Run many times per day/hour in production | Efficiency + Consistency | Cost compounds at volume, and a skill that's right 60% of the time is worse than one that's predictably right or predictably wrong. |
   | Run rarely but high-stakes when it does | Correctness + Quality | Token cost barely matters once; getting it right does. |

   If a skill spans more than one row, default to this precedence order — **correctness > quality > efficiency > consistency** — since a wrong-but-cheap answer is worse than a right-but-slow one, and a right answer that's inconsistent is still more useful than a wrong one that's reliable. Override the default only with a stated reason tied to the skill's actual failure cost (e.g. a high-volume skill where a 2% correctness gap is cheap to tolerate but a latency spike breaks a downstream SLA) — either way, say which row(s) and precedence you used in the scope statement (Step 0's closing line). Don't silently default to "all four axes matter equally."
4. Is skill-creator's infrastructure available in this environment? Concretely: check for a `skill-creator` skill/plugin the same way you'd check for any other loaded skill — `/mnt/skills/*/skill-creator/` on claude.ai; a sibling entry under this project's skills/plugin directory on Claude Code; or, generically, whether a skill named `skill-creator` shows up when you list what's currently loaded/available. If none of those turn up a match, treat it as absent — don't guess or wait for it to appear. If yes, plan to reuse it per `references/skill-creator-integration.md`. If no, this skill's own `scripts/` provide fallbacks.

**Do NOT load** `references/skill-creator-integration.md`'s reuse table if skill-creator isn't present — jump straight to that file's "When skill-creator isn't available" section instead; the table above it describes infrastructure you won't be touching.

State this scope back to the user in a sentence or two before building anything — it's cheap to correct now and expensive to redo later.

**L0-only fast path:** If the request asks only for an input-layer report, set `scope.layers` to `["L0"]`, set `has_refinement_step` to `false`, omit L1/L2/L3 and baseline work, and exclude any unrequested axes. From *this* skill's own files, load only `agents/input-layer-judge.md`, `references/schemas.md`, and `references/layers-and-metrics.md` (the last one defines what L0's Correctness/Quality axes actually mean, which the Description Accuracy check depends on) — you already have `SKILL.md` open to be reading this. Skip `references/scientific-method.md`, `references/skill-creator-integration.md`, and `references/skill-design-primer.md`, none of which L0 scoring needs. This does NOT shrink what you read of the *target* skill: `agents/input-layer-judge.md`'s own scoping note is explicit that D1, D2, D3, D4, D6, and D8 all draw on the target's bundled `agents/`/`references/`/`scripts/` content, not just its `SKILL.md` — the fast path trims skill-evaluator's own reference overhead, not the object being scored. Write `l0_scores.json` and its Markdown rendering. Do not create L1 assertions or run-output records.

### Step 1: Pre-register the hypothesis and assertions

Before running anything:
- Write down what you expect to see and why ("v2's more explicit error-handling instructions should raise correctness on malformed-input test cases without adding much token overhead").
- Write correctness assertions for L1 (and L2, if it exists) *before* looking at any actual output. This is the single most important scientific-hygiene step in this whole skill — assertions written after seeing outputs tend to unconsciously fit what already happened, which defeats the point of having them.
- Decide N (repeats per test case) up front. N=1 tells you nothing about consistency. N=3 is a reasonable default; go higher (5–10) for anything with high stakes or known flakiness.
- Log all of this in `evals/eval_plan.json` — see `references/schemas.md` for the shape. This is what makes the eval reproducible and extensible: six months from now, someone (including you) should be able to read this file and know exactly what was being tested and why.

The pre-registration and control rationale is documented in `references/scientific-method.md`; keep the plan explicit even when a requested scope omits L1 or later layers.

**Gate — do not proceed past this step without `evals/eval_plan.json` on disk.** Check it exists before running anything in Step 2 or Step 3, not after. If you find L1 output already sitting in a workspace with no `eval_plan.json` anywhere for it, that run's pre-registration discipline was never satisfied — say so plainly rather than writing an `eval_plan.json` now to match output you've already seen (that's the exact violation the Non-Negotiables warn against, just committed after the fact instead of before). The honest move is to flag the gap and either discard the un-preregistered run or treat it as informal/exploratory data, never as a validated result — and if you keep it, drop a `PRE_REGISTRATION_STATUS.json` (`{"status": "informal_exploratory", "reason": "..."}`) directly in that `run-<n>/` directory so `scripts/aggregate_layered.py` (which skips any run carrying that marker) can never silently fold it into a statistical summary later. A note *about* the gap somewhere else isn't enough — the marker has to live where the aggregator will actually look.

### Step 2: Run L0 — score the input layer

*Axes in play: correctness and quality only — L0 has no per-run efficiency or consistency score (see the grid above; there's no "run" to time or repeat at this layer).*

Before spending compute on L1/L2 runs, sanity-check the input itself. A skill can fail purely because its description undertriggers, or its instructions are ambiguous; the scientific-method rationale for this gate is in `references/scientific-method.md`.

Use `agents/input-layer-judge.md`, which scores two separate artifacts:
- **The full 8-dimension, 990-point skill-quality rubric (D1–D8)** — score all eight, not just D4. D4 (Description Quality) is the one most directly about triggering: would this description fire reliably on realistic queries, including near-miss negatives? (If skill-creator is present, its "Description Optimization" trigger-eval loop is the more rigorous version of that D4 check specifically — defer to it when available.)
- **Instruction clarity**, **test prompt realism**, and **description accuracy** (the file's separate "Eval-Design Checks" section, 1–5 each): are steps unambiguous enough that two independent runs would take the same approach, are the L1 test prompts things a real user would actually type, and — distinct from D4's triggering quality — does the description's claims actually hold up against what the skill's body/bundle implements?

Record scores in `evals/l0_scores.json` (`dimensions` + `eval_design_checks`, per `references/schemas.md`).

**Checkpoint — stop here if L0 is weak.** If `dimensions.total_score` is a clear fail (D grade or below) or any *numerically-scored* `eval_design_checks` entry is ≤2, don't proceed into Step 3. A check reported as `"skipped"` (e.g. Test Prompt Realism with no `eval_plan.json` prompts yet to judge) has no score to compare against ≤2 and does **not** trip this gate — it's a "nothing to measure yet" state, not a "measured and it's weak" one; don't force a number on it just to make the gate's condition well-defined. Flag the specific gap to the user and get a decision: fix it now, or proceed anyway with the gap noted as a caveat on every L1/L2 result that follows. Running an N-repeat L1 batch against instructions or prompts already known to be weak just measures noise at N× the cost — the same reasoning as Step 0's checkpoint, applied to the layer this skill exists to catch cheaply.

### Step 3: Run L1 — raw output

*Axes in play: all four — correctness, quality, efficiency, and consistency (consistency only resolves once N≥3 repeats are in; a single run gives you a point estimate, not a consistency score).*

For each test prompt, run N repeats with the skill active (and, where relevant, N baseline repeats without the skill / with the prior version — see `references/layers-and-metrics.md` for when a baseline is worth the cost).

Grade each run's correctness against the pre-registered assertions. Correctness grading is mechanical (read the assertion, check the artifact, pass/fail/null) — there's no judgment call here about *which* grader to prefer, only *whether one is reachable*: use skill-creator's `agents/grader.md` when reachable, since it's the more actively maintained of the two identical-output-shape implementations; otherwise use this skill's own `agents/grader.md` as the fallback. **Do NOT load both** — they'd just grade the same run twice against the same rules for no additional signal. For quality, use this ordered fallback: (1) `agents/manual-tc-quality-judge.md` when the skill writes manual test cases, (2) skill-creator's quality-rubric judge when reachable for another skill type, or (3) `agents/generic-quality-judge.md` — it doesn't carry a fixed rubric itself, but it defines the discipline for writing and pre-registering one into `eval_plan.json`'s `scope.quality_rubric` from the concerns named in Step 0.3, before any output exists. **`agents/input-layer-judge.md` is L0-only** and must not grade L1/L2 output. Capture tokens/time/tool-calls per run.

Save per-run results in `<workspace>/L1/<eval-id>/run-<n>/` following `references/schemas.md`.

**If Step 0 scoped this as an A/B comparison** (two skill versions, or with_skill vs. without_skill): do not grade each configuration independently with its label visible, the way the paragraph above describes — that defeats the blinding `references/scientific-method.md` rule 4 requires. Instead, run N repeats (same N as Step 1) feeding both configurations' raw outputs to `agents/comparator.md`, labeled only "A" and "B" each time; it performs its own blind grading pass and returns the comparison directly (registered as `version_ab_delta` in `metrics_registry.json`). Its output doesn't fit the per-configuration `result.json` shape in `references/schemas.md` — save each repeat at `<workspace>/L1/<eval-id>/run-<n>/ab-comparison.json` (same `run-<n>` convention as `result.json`, so N≥3 repeats aggregate into a real consistency read rather than a single-sample verdict) and carry the aggregated result into Step 6's report as its own section, the same way L3's delta sits alongside L1/L2 rather than inside them. `scripts/aggregate_layered.py` parses this shape automatically.

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

Save its output at `<workspace>/L3/<eval-id>/refinement-analysis.json` (see `references/schemas.md`) — this is the qualitative companion to `compute_l3_delta`'s numeric `l3_delta`, not a replacement for it.

This is the piece most eval setups skip, and it's usually where the most actionable insight lives — it tells you whether your *review process*, not just your skill, is pulling its weight.

### Step 6: Aggregate and report

Aggregate into a layer-tagged benchmark file (`references/schemas.md` extends skill-creator's `benchmark.json` with a `layer` field, so its existing viewer/aggregator can be reused with a small adapter — see `scripts/aggregate_layered.py`). Report, per layer:
- Correctness: pass rate, mean ± stddev across N
- Quality: mean rubric score ± stddev
- Efficiency: mean tokens/time ± stddev
- Consistency: stddev itself, called out explicitly — high variance is a finding, not noise to average away

If skill-creator's `eval-viewer` is available, reuse it (it already renders prompt/output/grades/feedback side by side and reads the same field names this skill writes). Otherwise present results directly in conversation, one test case at a time.

Fill in `benchmark.json`'s `hypothesis_check` before calling the report done: did the result match what the pre-registered hypothesis predicted (`matched_expectation`), and if not, is it `surprising`? A `surprising: true` result gates Step 7 — re-run before reporting it (per the Non-Negotiables), and only set `rerun_completed: true` once that's actually happened; don't finalize a report with a surprising result and `rerun_completed: null`.

Report `evals[].exploratory_assertions[]` (if any exist) in their own clearly-labeled subsection, separate from the pre-registered results above — never blend a late-noticed observation into the correctness/quality numbers it wasn't part of pre-registering. An exploratory finding is material for the *next* `eval_plan.json`, not evidence for this one's hypothesis.

### Step 7: Iterate, and grow the registry

Diagnose from the earliest layer that failed, not from wherever the numbers happen to look worst — an L1 failure caused by an L0 defect will keep failing no matter how many times you re-run L1:

| Evidence | Diagnosis | Fix |
|---|---|---|
| The skill wouldn't trigger for a realistic request | L0 description defect | Rewrite the description, re-run the L0 pass — don't touch L1 |
| Independent runs took different approaches for the same prompt | L0 instruction ambiguity | Tighten the instruction or add a decision rule, re-run L0's Instruction Clarity check |
| Assertions fail but the instruction/prompt were clear | L1 execution or knowledge gap | Read the actual output, revise the skill's content or logic, then re-run L1 |
| L2 changed wording but not which assertions pass | Refinement is polish, not substance | Report the cost honestly (per the Non-Negotiables) — don't count it as a correctness win |

Re-run only the layer the fix targets, then compare against the pre-registered hypothesis (did it hold?). Any new metric you found yourself wanting mid-evaluation — add it to `references/metrics_registry.json` rather than hard-coding it into a one-off script, so the next evaluation (of this skill or any other) can pick it up. See "Extending this framework" below.

---

## Extending this framework

The framework is deliberately built around one seam: **the metric registry** (`references/metrics_registry.json`). Each entry declares:
- `name` and `axis` (an array — one or more of correctness / quality / efficiency / consistency)
- `applies_to_layers`: which of L0/L1/L2/L3 it's meaningful for
- `scorer_type`: `assertion` (script-checkable), `rubric` (needs a blind judge), or `derived` (computed from other metrics, e.g. anything in L3)
- a pointer to the scoring logic (a script in `scripts/`, or a prompt in `agents/`)

To add a new evaluation dimension later (say, "hallucination rate" or "style consistency with a brand guide"): write the scorer, add one registry entry, done — the workflow steps above don't change. This is what makes the framework extensible to skills this design didn't anticipate: the four-layer/four-axis grid stays fixed, only the registry grows.

To extend to a *general-purpose* evaluator for arbitrary skills (not just the one you're starting with): the only skill-specific parts of this whole framework are (a) the test prompts, (b) the assertions, and (c) whether L2 exists. Everything else — the layer model, the axes, the statistical treatment, the registry mechanism — is already skill-agnostic. Generalizing later mainly means templating Step 0's scoping questions rather than restructuring anything.

## Reference files

Every conditional load rule mentioned inline through the Workflow above is collected here too, so there's one place to check instead of re-scanning each step:

| File | Purpose | Do NOT load when |
|---|---|---|
| `references/layers-and-metrics.md` | Full definition of the four-layer object model, worked examples, which axes apply to which layers | — (read before designing any eval; no exclusion condition) |
| `references/scientific-method.md` | The methodology rules (pre-registration, blinding, controls, sample size) in depth, with rationale | Running the L0-only fast path (Step 0) — the Non-Negotiables' "Also assumed" line covers the enforcement points inline without needing the full reasoning |
| `references/schemas.md` | JSON schemas for `eval_plan.json`, `l0_scores.json`, layer-tagged run/benchmark/`ab-comparison.json` files, `metrics_registry.json` | — (needed whenever writing any of these files) |
| `references/skill-creator-integration.md` | Which skill-creator files to reuse vs. what this skill adds | Skill-creator is absent — its own "When skill-creator isn't available" section is the only part that still applies |
| `references/skill-design-primer.md` | The Value Equation and Expert/Activation/Redundant content model D1's scoring protocol tags sections with, plus a 9-pattern failure-mode catalog behind `agents/input-layer-judge.md`'s rubric | Scoring L0 — the rubric tables are self-sufficient; this is for authoring a new skill or wanting the reasoning, not for grading an existing one |
| `agents/input-layer-judge.md` | Rubric and instructions for scoring L0 (description/instructions/prompt quality) | — (required for every L0 pass) |
| `agents/grader.md` | Fallback assertion grader for L1/L2 correctness | Skill-creator's own `grader.md` is reachable — they produce the same output, loading both wastes context |
| `agents/manual-tc-quality-judge.md` | Quality judge for skills that write manual test cases (registered as `manual_tc_quality_score`) | The skill under test isn't a test-case writer |
| `agents/generic-quality-judge.md` | Grading discipline (not a fixed rubric) for pre-registering and applying a quality rubric to any skill type not covered by `manual-tc-quality-judge.md` or a skill-creator judge (registered as `rubric_quality_score`) | The skill under test writes manual test cases (use `manual-tc-quality-judge.md` instead), or skill-creator's own quality judge is reachable |
| `agents/refinement-analyzer.md` | Computes the L1→L2 delta | Step 0 found no real refinement step — there's no L2 to delta against |
| `agents/comparator.md` | Blind A/B fallback comparing two skill *versions'* outputs at the same layer (registered as `version_ab_delta`); distinct from `refinement-analyzer.md`, which compares L1 vs L2 within one version | Skill-creator's own `agents/comparator.md` + `agents/analyzer.md` are reachable, or Step 0 isn't doing an A/B comparison at all |
| `scripts/aggregate_layered.py` | Aggregates layer-tagged run data into statistics (mean/stddev/delta per layer × axis); skips any run marked `PRE_REGISTRATION_STATUS.json` | — (run once at Step 6, not "loaded" mid-workflow) |
| `scripts/check_consistency.py` | Maintenance linter for this skill's own bundle — catches dangling file references, rule citations pointing at renumbered/removed rules, malformed `metrics_registry.json` entries, and two specific stale patterns this framework has hit before (the D7 pattern enum, the eval-design-checks count). Not part of scoring any target skill — run it after editing anything in *this* skill's own `SKILL.md`/`agents/`/`references/`, before trusting the edit | Scoring any target skill (it only checks this skill's own bundle, never the one being evaluated) |
