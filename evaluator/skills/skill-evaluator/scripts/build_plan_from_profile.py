#!/usr/bin/env python3
"""
Turns a filled-in assessment profile (profiles/<name>/criteria.json + baseline.json)
into pre-registered content for evals/eval_plan.json.

What it generates (all before any trainee output is read, per SKILL.md Step 1):
  - one correctness assertion per required baseline scenario   (id "scn:<id>")
  - one correctness assertion per required verification point  (id "vp:<id>")
  - one correctness assertion per `check` criterion            (id "chk:<id>")
  - scope.quality_rubric from every `rubric` criterion

It refuses to run while any value still starts with "TODO", so an unfilled
skeleton can never be pre-registered by accident. It does not decide whether
the criteria are good -- only that they are complete and well-formed.

Usage:
    python scripts/build_plan_from_profile.py profiles/manual-qa \
        --skill-name trainee-01 --hypothesis "..." --out evals/eval_plan.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = {"positive", "negative", "boundary"}
PARTS = ("general_l0", "rubric", "coverage", "checks")
L0_DIMS = {f"D{i}" for i in range(1, 9)}
OVERRIDE_CHANGES = {"weight", "anchors"}


def walk_todos(node, path=""):
    if isinstance(node, str) and node.strip().upper().startswith("TODO"):
        yield path
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_todos(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_todos(v, f"{path}[{i}]")


def validate(criteria, baseline):
    problems = []
    for label, doc in (("criteria.json", criteria), ("baseline.json", baseline)):
        problems += [f"{label}: unfilled TODO at {p}" for p in walk_todos(doc)]

    seen = set()
    for c in criteria.get("criteria", []):
        cid = c.get("id")
        if cid in seen:
            problems.append(f"criteria.json: duplicate id {cid}")
        seen.add(cid)
        if c.get("type") == "rubric":
            if set(c.get("anchors", {})) != {"1", "3", "5"}:
                problems.append(f"criteria.json: {cid} needs anchors for exactly 1, 3, 5")
            if not isinstance(c.get("weight"), (int, float)) or c["weight"] <= 0:
                problems.append(f"criteria.json: {cid} needs a positive numeric weight")
            if c.get("gate_min") is not None and c["gate_min"] not in (1, 2, 3, 4, 5):
                problems.append(f"criteria.json: {cid} gate_min must be 1-5 or omitted")
        elif c.get("type") == "check":
            if not c.get("text"):
                problems.append(f"criteria.json: {cid} (check) needs `text`")
        else:
            problems.append(f"criteria.json: {cid} has type {c.get('type')!r}, must be rubric or check")

    scn_ids = set()
    for s in baseline.get("scenarios", []):
        sid = s.get("id")
        if sid in scn_ids:
            problems.append(f"baseline.json: duplicate scenario id {sid}")
        scn_ids.add(sid)
        if s.get("category") not in CATEGORIES:
            problems.append(f"baseline.json: {sid} category must be one of {sorted(CATEGORIES)}")
        if not s.get("verification_points"):
            problems.append(f"baseline.json: {sid} has no verification_points")
    weights = criteria.get("overall", {}).get("weights", {})
    if set(weights) != set(PARTS):
        problems.append(f"criteria.json: overall.weights must have exactly {list(PARTS)}")
    else:
        for part, w in weights.items():
            if not isinstance(w, (int, float)) or w < 0:
                problems.append(f"criteria.json: overall.weights.{part} must be a number >= 0")
        if all(isinstance(w, (int, float)) for w in weights.values()) and sum(weights.values()) <= 0:
            problems.append("criteria.json: overall.weights must not all be 0")
    kinds = {c.get("type") for c in criteria.get("criteria", [])}
    if weights.get("rubric") and "rubric" not in kinds:
        problems.append("criteria.json: overall.weights.rubric > 0 but there are no rubric criteria")
    if weights.get("checks") and "check" not in kinds:
        problems.append("criteria.json: overall.weights.checks > 0 but there are no check criteria")
    seen_dims = set()
    for o in criteria.get("l0_overrides", []):
        d = o.get("dimension")
        if d not in L0_DIMS:
            problems.append(f"criteria.json: l0_overrides dimension {d!r} must be one of D1..D8")
        if d in seen_dims:
            problems.append(f"criteria.json: l0_overrides has {d} twice")
        seen_dims.add(d)
        if o.get("change") not in OVERRIDE_CHANGES:
            problems.append(f"criteria.json: override {d} change must be one of {sorted(OVERRIDE_CHANGES)}")
        elif o["change"] == "weight" and not (isinstance(o.get("weight"), (int, float)) and o["weight"] > 0):
            problems.append(f"criteria.json: override {d} needs a positive numeric weight")
        elif o["change"] == "anchors" and set(o.get("anchors", {})) != {"1", "3", "5"}:
            problems.append(f"criteria.json: override {d} needs anchors for exactly 1, 3, 5")
        if not o.get("reason"):
            problems.append(f"criteria.json: override {d} needs a reason")
    if not criteria.get("criteria"):
        problems.append("criteria.json: no criteria")
    if not baseline.get("scenarios"):
        problems.append("baseline.json: no scenarios")
    return problems


def build_assertions(criteria, baseline):
    out = []
    for s in baseline["scenarios"]:
        if s.get("required", True):
            out.append({
                "id": f"scn:{s['id']}",
                "text": f"The output contains at least one test case that covers scenario \"{s['title']}\": {s['description']}",
                "pre_registered": True,
                "critical": bool(s.get("critical", False)),
            })
        for v in s["verification_points"]:
            if v.get("required", True):
                out.append({
                    "id": f"vp:{v['id']}",
                    "text": f"A test case for scenario \"{s['title']}\" has an expected result that verifies: {v['expected']}",
                    "pre_registered": True,
                    "critical": bool(v.get("critical", False)),
                })
    for c in criteria["criteria"]:
        if c["type"] == "check":
            out.append({"id": f"chk:{c['id']}", "text": c["text"], "pre_registered": True,
                        "critical": bool(c.get("critical", False))})
    return out


def build_rubric(criteria):
    dims = {}
    for c in criteria["criteria"]:
        if c["type"] == "rubric":
            dims[c["name"]] = {
                **c["anchors"],
                "weight": c["weight"],
                "gate_min": c.get("gate_min"),
                "instant_low_flag": c.get("instant_low_flag"),
            }
    return dims


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile_dir", type=Path)
    ap.add_argument("--skill-name", required=True)
    ap.add_argument("--skill-version", default="final")
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--n-repeats", type=int, default=1)
    ap.add_argument("--has-refinement", action="store_true",
                    help="trainee submitted a refined version (real L2)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    criteria = json.loads((args.profile_dir / "criteria.json").read_text(encoding="utf-8"))
    baseline = json.loads((args.profile_dir / "baseline.json").read_text(encoding="utf-8"))

    problems = validate(criteria, baseline)
    if problems:
        print(f"build_plan_from_profile: {len(problems)} problem(s), nothing written:\n")
        for p in problems:
            print(f"  - {p}")
        return 1

    layers = ["L0", "L1"] + (["L2", "L3"] if args.has_refinement else [])
    plan = {
        "skill_name": args.skill_name,
        "skill_version": args.skill_version,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": args.hypothesis,
        "scope": {
            "layers": layers,
            "has_refinement_step": args.has_refinement,
            "refinement_mechanism": "trainee-submitted refined version" if args.has_refinement else None,
            "primary_axes": ["correctness", "quality"],  # consistency and efficiency out of scope
            "n_repeats": args.n_repeats,
            "assessment": {
                "overall_weights": criteria["overall"]["weights"],
                "l0_overrides": criteria.get("l0_overrides", []),
            },
            "quality_rubric": {
                "source": f"profiles/{args.profile_dir.name}/criteria.json v{criteria.get('version')}",
                "dimensions": build_rubric(criteria),
            },
        },
        "baseline": {
            "type": "assessment_baseline",
            "reference": f"profiles/{args.profile_dir.name}/baseline.json "
                         f"assessment {baseline.get('assessment_id')} v{baseline.get('version')}",
        },
        "evals": [{
            "id": 1,
            "name": baseline["assessment_id"],
            "prompt": f"See requirement source: {baseline['requirement_source']}",
            "files": [baseline["requirement_source"]],
            "assertions": build_assertions(criteria, baseline),
            "exploratory_assertions": [],
        }],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}: {len(plan['evals'][0]['assertions'])} assertions, "
          f"{len(plan['scope']['quality_rubric']['dimensions'])} rubric dimensions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
