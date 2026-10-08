# Assessment Profiles

A profile is the seam for evaluating many trainees against **one fixed definition of "good"**. The course owner supplies two data files; the framework does the rest. Nothing in `SKILL.md`'s workflow changes per assessment, and no judge prompt has to be edited when criteria change.

Only `manual-qa` exists today. A new area is a new folder under `profiles/` with the same two files, plus a judge agent if the existing one doesn't fit.

## The two files

| File | Holds | Filled from |
|---|---|---|
| `profiles/<name>/criteria.json` | Groups (A/B/C), the criteria in them, the pass threshold, and the L0 override | The course's rubric Excel (currently `QA_AI_Skills_Assessment_Rubric_MANUAL.xlsx`, in progress) |
| `profiles/<name>/baseline.json` | The answer key: acceptance criteria, ambiguities (mandatory or not), edge cases, planted bugs with severity, `severity_scale`, the percentage thresholds the criteria refer to, and the environment info the exam provided | The assessment author |

`criteria.json` is reused across assessments; `baseline.json` belongs to one assessment. Both carry a `version`. `baseline.json` ships as a skeleton full of `TODO`; `scripts/build_plan_from_profile.py` refuses to run while any `TODO` remains.

## Scoring model

Every criterion is `deduction` type: `max_points`, `penalty_per_error`, and a `details` text that states what passes and what counts as an error.

- criterion points = `max_points` − `penalty_per_error` × errors, floored at 0
- the **judge reports error counts only**; `scripts/render_assessment_report.py` computes points, so grading is not bent by knowing the pass line
- group total = sum of its criteria; total = sum of groups; **PASS at `pass_threshold`** (70 of 100 for manual-qa)
- a criterion that meets its `na_when` condition scores full points and is flagged in the report. This is a choice: the trainee is not penalised for a criterion that does not apply. Change it in the script if the course wants N/A criteria dropped from the total instead.

## Groups and layers

| Group | Content | Layer |
|---|---|---|
| A | The trainee's skill set (A1–A8) | L0, **replaces D1–D8** |
| B | Workflow provenance from the chat transcript (B1–B4) | L1 |
| C | Output quality against the answer key (C1–C7) | L1 (L2 when scored) |

Trainee submission → layer: final skills → L0; chat prompts and transcript → evidence for L0 and B; **first manual-QA output in the chat log → L1**; refined version → L2; L3 = L2 − L1 via `agents/refinement-analyzer.md`. Each trainee is one sample (`n_repeats: 1`), so consistency is not measured and no consistency claim may be made.

Open point: the rubric scores a single output. Whether B (provenance) applies to L2, where hand edits are allowed, is not defined yet; until it is, score L2 on group C only.

## L0 override

`criteria.json` → `l0_override: {"mode": "replace", "group": "A", "reason": "..."}`. When present, group A **replaces** D1–D8: `agents/input-layer-judge.md` does not score them, and A1–A8 are graded by `agents/manual-qa-assessment-judge.md`. The override is copied into `eval_plan.json` at pre-registration. No override means D1–D8 apply as usual.

## Advisory flags and human decisions

A criterion may carry `advisory` entries (today, C6: `C6-severity`, severity more than one level from the key on `severity_scale`). For these the agent only **flags**, with the bug ID, the trainee's severity and the key's. A flag costs nothing and the report is `provisional` until a human decides. The human records:

```json
{"C6-severity:BUG-02": {"decision": "fail", "errors": 1}}
```

and passes it with `--human`. `fail` adds `errors` (default 1) to C6; `pass` adds nothing. Re-run the script after deciding; the status becomes `final` when no flag is pending.

## Wiring it into a run

1. Fill the answer key in `baseline.json`; revise `criteria.json` if the rubric changed (edit the JSON; the Excel import was a one-off).
2. Pre-register: `python scripts/build_plan_from_profile.py profiles/manual-qa --skill-name <trainee> --hypothesis "<text>" [--has-refinement] --out evals/eval_plan.json`. The plan stores sha256 of both profile files, so a later edit is detectable.
3. Grade with `agents/manual-qa-assessment-judge.md` → `assessment_result.json`.
4. Report: `python scripts/render_assessment_report.py --plan evals/eval_plan.json --result <path> --out-dir report/ [--human decisions.json] [--submission-dir <submission root>]`. It writes `assessment_scoring_sheet.xlsx`, `assessment_report.md` and `assessment_report.json`.

## The scoring sheet

One row per criterion, laid out like the course's Excel scoring sheet:

| Column | Content |
|---|---|
| Category | The group (A Skill set, B Workflow coverage, C Output quality) |
| Sub-Category | Criterion id and name (e.g. `C4 TC quality`) |
| Evaluation Criteria | The criterion's `pass_when` |
| Max / Points / Errors | Points available, points earned, errors counted (human-decided flags included) |
| Evidence/Notes | One short line per deduction: an **evidence ref**, then a trimmed quote |
| Meets target? | `Yes` (no deduction), `No`, `N/A`, or `Pending human` |

Each group ends with a subtotal row, and the last row is the total against the pass threshold. Evidence refs use `path[:line]`, `path!Sheet!Cell` or `path#Heading`, relative to the submission root. With `--submission-dir` the script checks that each ref's file exists and marks it `(ref not found)` otherwise; a ref with no file path is marked `(no file ref)`. Both are also listed under Notes.

This sheet has no weight or skill/output 1-5 columns, because the manual-QA rubric scores by points and deductions. A profile with the weighted 1-5 model would need its own scoring model before it can use the same renderer.

## What the profile does not do

- It does not judge whether the criteria are good. That is the course owner's call.
- It does not match anything by string comparison. Whether a question covers an ambiguity, or a bug matches a BUG-xx, is a semantic judgment by the judge with a quoted `where`/`quote` for every error.
- Do not append post-hoc criteria to a generated plan. Anything noticed later goes in `exploratory_assertions[]`, or in `grading_notes` for the next profile version.
