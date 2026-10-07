# Assessment Profiles

A profile is the seam for evaluating many trainees against **one fixed definition of "good"**. The course owner supplies two data files; the framework does the rest. Nothing in `SKILL.md`'s workflow changes per assessment, and no judge prompt has to be edited.

Only `manual-qa` exists today. A new area (e.g. `automation-qa`) is a new folder under `profiles/` with the same two files, plus a judge agent if the existing one doesn't fit.

## The two files

| File | Holds | Filled from |
|---|---|---|
| `profiles/<name>/criteria.json` | The scoring criteria. `rubric` type = scored 1–5 with anchors at 1/3/5, a weight, and an optional instant-low flag. `check` type = one binary statement. | The course's Excel criteria sheet |
| `profiles/<name>/baseline.json` | What the output must contain: required scenarios (positive / negative / boundary), each with its required verification points | The assessment author's answer key |

Both ship as **skeletons full of `TODO` strings**. `scripts/build_plan_from_profile.py` refuses to run while any `TODO` remains, so an unfilled skeleton cannot be pre-registered by accident. Bump `version` in each file whenever it changes; the version is copied into `eval_plan.json` so a result always says which criteria produced it.

**Why criteria and baseline are separate files:** criteria are reused across every assessment; a baseline belongs to one assessment. Swapping in a new assessment means replacing one file and leaving the other alone.

## Mapping a trainee submission onto the layers

| Trainee submits | Layer | How it is used |
|---|---|---|
| Final skill set | **L0** | Scored by `agents/input-layer-judge.md` as the target skill |
| Chat prompts used with AI | **L0 context** | Read as evidence of how the skills were exercised; also the source for what "raw" means below. Not scored on its own. |
| First manual-QA output produced from the assessment (raw) | **L1** | Graded by `agents/manual-qa-assessment-judge.md` |
| Refined version | **L2** | Graded by the same judge with the same plan, so L1 and L2 stay comparable; L3 = L2 − L1 via `agents/refinement-analyzer.md` |

Decided: the raw L1 is the first manual-QA output in the trainee's chat log, and L2 is the refined version they submit. Each trainee is one sample (`--n-repeats 1`, the script default), so consistency is not measured and the report must not make any consistency claim. `aggregate_layered.py` already reports `stddev: null` for N=1.

## Wiring it into a run

1. Fill `criteria.json` and `baseline.json`.
2. Pre-register: `python scripts/build_plan_from_profile.py profiles/manual-qa --skill-name <trainee> --hypothesis "<text>" [--has-refinement] --out evals/eval_plan.json`. This writes the scenario/verification-point/check assertions and `scope.quality_rubric`.
3. Grade each L1/L2 output with `agents/manual-qa-assessment-judge.md`; results land in the usual `result.json` shape plus a `correctness.coverage` block.
4. Aggregate with `scripts/aggregate_layered.py` unchanged.

## One overall score, four visible parts

`scripts/render_assessment_report.py --plan ... --l0 ... --result ... --out-dir ...` writes `assessment_report.json` and `.md`. Four parts, each 0-100, combined by the weights in `criteria.json` → `overall.weights`:

| Part | From | Notes |
|---|---|---|
| `general_l0` | skill-evaluator's D1-D8, **final** scores | override `weight` entries apply here |
| `rubric` | the profile's `rubric` criteria | weighted by each criterion's `weight` |
| `coverage` | baseline scenarios + verification points | passed / gradeable |
| `checks` | the profile's `check` criteria | passed / gradeable |

The report always shows all four next to the overall number, so a high total cannot hide a weak part.

**Overrides** (`criteria.json` → `l0_overrides`): D1-D8 only, `change` is `weight` (D counts more or less in `general_l0`) or `anchors` (that D is scored against the profile's 1/3/5 text; the L0 judge records default and final, and the final one is what counts). Every override needs a `reason`.

**Gates:** mark a baseline scenario or verification point `"critical": true`, a check `"critical": true`, or a rubric criterion `"gate_min": N`. A critical miss sets that whole part (`coverage` or `checks`) to 0; a rubric dimension under `gate_min` contributes 0. A gate zeroes only the criterion it belongs to, not the other parts. Gates are applied by the script, not by the graders.

**Weights are pre-registered.** They are copied into `eval_plan.json` by `build_plan_from_profile.py`. Change them only by revising the profile and regenerating the plan before grading, never after seeing outputs.

## What the profile does not do

- It does not judge whether the criteria are good. That is the course owner's call.
- It does not match scenarios by string comparison. Whether a test case "covers" a scenario is a semantic judgment, made by the judge with quoted evidence.
- Do not append post-hoc assertions to the generated plan. Anything noticed later goes in `exploratory_assertions[]`, as always.
