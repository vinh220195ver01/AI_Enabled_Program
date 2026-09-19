# JSON Schemas

These schemas extend (and stay compatible with) skill-creator's `evals.json`, `grading.json`, and `benchmark.json` where noted, adding the layer dimension and the new L0/L3 concepts. If skill-creator's viewer/aggregator is present, layer-tagged files here are designed to still work with it — see `skill-creator-integration.md`.

---

## eval_plan.json

The pre-registration record from Step 1. Written before any run happens.

```json
{
  "skill_name": "example-skill",
  "skill_version": "v2",
  "created_at": "2026-09-19T10:00:00Z",
  "hypothesis": "v2's explicit error-handling instructions should raise correctness on malformed-input cases without materially increasing token cost.",
  "scope": {
    "layers": ["L0", "L1", "L2", "L3"],
    "has_refinement_step": true,
    "refinement_mechanism": "human feedback via eval-viewer, one revision pass",
    "primary_axes": ["correctness", "quality"],
    "n_repeats": 3
  },
  "baseline": {
    "type": "previous_version",
    "reference": "v1"
  },
  "evals": [
    {
      "id": 1,
      "name": "malformed-csv-input",
      "prompt": "User's task prompt, written realistically",
      "files": [],
      "assertions": [
        {"id": "a1", "text": "Output flags the malformed row instead of silently dropping it", "pre_registered": true},
        {"id": "a2", "text": "Output includes a corrected CSV file", "pre_registered": true}
      ]
    }
  ]
}
```

**Fields:**
- `hypothesis`: free text, written before running anything
- `scope.layers`: which of L0/L1/L2/L3 apply to this evaluation — omit L2/L3 if there's no real refinement step
- `scope.has_refinement_step` / `refinement_mechanism`: forces an explicit statement of whether L2 is real or would be synthetic
- `scope.n_repeats`: N, fixed before running
- `baseline`: what L1 (and L2, if present) is compared against
- `evals[].assertions[].pre_registered`: `true` for assertions written before seeing output; any assertion added later must be `false` and goes in a separate exploratory list, never silently merged in

---

## l0_scores.json

Output of the input-layer judge (Step 2).

```json
{
  "skill_name": "example-skill",
  "skill_version": "v2",
  "description_quality": {
    "score": 4,
    "notes": "Triggers well on direct requests; borderline on implicit near-misses involving adjacent file types."
  },
  "instruction_clarity": {
    "score": 5,
    "notes": "Steps are unambiguous; two independent readings converged on the same approach."
  },
  "prompt_realism": {
    "score": 4,
    "notes": "Prompts are realistic but could include more casual/typo'd phrasing variants."
  },
  "flagged_issues": [
    "Step 3 says 'handle appropriately' with no further detail — candidate ambiguity."
  ]
}
```

---

## Layer-tagged run record

One file per run, extending skill-creator's `grading.json` with a `layer` field. Located at `<workspace>/<layer>/<eval-id>/run-<n>/result.json`.

```json
{
  "eval_id": 1,
  "eval_name": "malformed-csv-input",
  "layer": "L1",
  "configuration": "with_skill",
  "run_number": 1,
  "correctness": {
    "expectations": [
      {"text": "Output flags the malformed row instead of silently dropping it", "passed": true, "evidence": "..."},
      {"text": "Output includes a corrected CSV file", "passed": true, "evidence": "..."}
    ],
    "pass_rate": 1.0
  },
  "quality": {
    "rubric": {"clarity": 4, "completeness": 5},
    "overall_score": 4.5,
    "judge_notes": "Clear explanation of what was flagged and why."
  },
  "efficiency": {
    "tokens": 3800,
    "duration_seconds": 24.1,
    "tool_calls": 6
  }
}
```

`layer` is one of `L0` (rare — L0 doesn't usually get per-run records), `L1`, `L2`. `configuration` follows skill-creator's convention (`with_skill` / `without_skill`, or version identifiers when comparing two versions).

---

## Layer-tagged benchmark.json

Extends skill-creator's `benchmark.json` (see that skill's `references/schemas.md` for the base shape) by adding `layer` alongside `configuration` in every run record and in `run_summary`, and adding an `l3_delta` section.

```json
{
  "metadata": {
    "skill_name": "example-skill",
    "layers_evaluated": ["L1", "L2"],
    "n_repeats": 3
  },
  "run_summary": {
    "L1": {
      "with_skill": {
        "correctness": {"mean": 0.85, "stddev": 0.05},
        "quality": {"mean": 4.2, "stddev": 0.3},
        "efficiency_tokens": {"mean": 3800, "stddev": 400}
      }
    },
    "L2": {
      "with_skill": {
        "correctness": {"mean": 0.95, "stddev": 0.03},
        "quality": {"mean": 4.6, "stddev": 0.2},
        "efficiency_tokens": {"mean": 5200, "stddev": 500}
      }
    }
  },
  "l3_delta": {
    "correctness_delta": "+0.10",
    "quality_delta": "+0.4",
    "extra_cost_tokens": "+1400",
    "verdict": "Refinement meaningfully improved correctness and quality; extra token cost (37%) is justified given the correctness gain fixes a real defect class, not just wording polish.",
    "worth_it": true
  },
  "notes": []
}
```

---

## metrics_registry.json

The extensibility seam — see main SKILL.md "Extending this framework."

```json
{
  "metrics": [
    {
      "name": "assertion_pass_rate",
      "axis": "correctness",
      "applies_to_layers": ["L1", "L2"],
      "scorer_type": "assertion",
      "scorer_ref": "agents/grader.md"
    },
    {
      "name": "rubric_quality_score",
      "axis": "quality",
      "applies_to_layers": ["L0", "L1", "L2"],
      "scorer_type": "rubric",
      "scorer_ref": "agents/input-layer-judge.md"
    },
    {
      "name": "token_efficiency",
      "axis": "efficiency",
      "applies_to_layers": ["L1", "L2"],
      "scorer_type": "derived",
      "scorer_ref": "scripts/aggregate_layered.py"
    },
    {
      "name": "run_variance",
      "axis": "consistency",
      "applies_to_layers": ["L1", "L2"],
      "scorer_type": "derived",
      "scorer_ref": "scripts/aggregate_layered.py"
    },
    {
      "name": "refinement_delta",
      "axis": "correctness,quality,efficiency",
      "applies_to_layers": ["L3"],
      "scorer_type": "derived",
      "scorer_ref": "agents/refinement-analyzer.md"
    }
  ]
}
```

To add a metric later (example: "hallucination_rate"): append an entry with `name`, `axis`, `applies_to_layers`, `scorer_type`, and `scorer_ref` pointing to a new script or agent prompt. Nothing else in the framework needs to change.
