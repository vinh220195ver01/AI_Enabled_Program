#!/usr/bin/env python3
"""
Turns a filled-in assessment profile (profiles/<name>/criteria.json + baseline.json)
into the pre-registered evals/eval_plan.json (SKILL.md Step 1).

Scoring model of a profile: every criterion is `deduction` type -- it has
max_points and penalty_per_error; its score is max_points minus penalty x errors,
floored at 0. Criteria belong to groups; the total is the sum of all criteria
and the assessment passes at or above `pass_threshold`.

What it checks before writing anything:
  - no value still starts with "TODO" (an unfilled skeleton is never pre-registered)
  - criterion ids are unique, each belongs to a declared group
  - each group's criteria add up to the group's max_points
  - pass_threshold <= total of all max_points
  - baseline: unique ids, bug severities inside severity_scale, thresholds present

It records sha256 of both profile files in the plan, so a later edit to the
criteria or the answer key after grading started is detectable.

Usage:
    python scripts/build_plan_from_profile.py profiles/manual-qa \
        --skill-name trainee-01 --hypothesis "..." --out evals/eval_plan.json

--baseline PATH uses a different answer key (e.g. a test fixture) together with the
profile's own criteria.json.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_THRESHOLDS = {"ambiguity_found_pct", "ambiguity_with_tr_pct", "bug_found_pct"}


def walk_todos(node, path=""):
    if isinstance(node, str) and node.strip().upper().startswith("TODO"):
        yield path
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_todos(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_todos(v, f"{path}[{i}]")


def dup_ids(items, label):
    seen, out = set(), []
    for it in items:
        if it.get("id") in seen:
            out.append(f"{label}: duplicate id {it.get('id')}")
        seen.add(it.get("id"))
    return out


def validate(criteria, baseline):
    problems = []
    for label, doc in (("criteria.json", criteria), ("baseline.json", baseline)):
        problems += [f"{label}: unfilled TODO at {p}" for p in walk_todos(doc)]

    groups = {g["id"]: g for g in criteria.get("groups", [])}
    problems += dup_ids(criteria.get("groups", []), "criteria.json groups")
    problems += dup_ids(criteria.get("criteria", []), "criteria.json criteria")
    if not criteria.get("criteria"):
        problems.append("criteria.json: no criteria")

    sums = {gid: 0 for gid in groups}
    for c in criteria.get("criteria", []):
        cid = c.get("id")
        if c.get("type") != "deduction":
            problems.append(f"criteria.json: {cid} type must be 'deduction'")
        if c.get("group") not in groups:
            problems.append(f"criteria.json: {cid} group {c.get('group')!r} is not declared in groups")
            continue
        for f in ("max_points", "penalty_per_error"):
            if not isinstance(c.get(f), (int, float)) or c[f] <= 0:
                problems.append(f"criteria.json: {cid} needs a positive numeric {f}")
        if not c.get("details"):
            problems.append(f"criteria.json: {cid} needs `details` (the grader reads it)")
        sums[c["group"]] += c.get("max_points") or 0
        for adv in c.get("advisory", []):
            if adv.get("decision") != "human" or not adv.get("id"):
                problems.append(f"criteria.json: {cid} advisory entries need an id and decision 'human'")
    for gid, g in groups.items():
        if sums[gid] != g.get("max_points"):
            problems.append(f"criteria.json: group {gid} criteria add up to {sums[gid]}, group max_points is {g.get('max_points')}")
    total = sum(g.get("max_points", 0) for g in groups.values())
    if not isinstance(criteria.get("pass_threshold"), (int, float)) or not 0 < criteria["pass_threshold"] <= total:
        problems.append(f"criteria.json: pass_threshold must be between 1 and the total {total}")
    ov = criteria.get("l0_override")
    if ov and (ov.get("mode") != "replace" or ov.get("group") not in groups or not ov.get("reason")):
        problems.append("criteria.json: l0_override needs mode 'replace', a declared group, and a reason")

    for key in ("acceptance_criteria", "ambiguities", "edge_cases", "bugs"):
        problems += dup_ids(baseline.get(key, []), f"baseline.json {key}")
        if not baseline.get(key):
            problems.append(f"baseline.json: {key} is empty")
    scale = baseline.get("severity_scale", [])
    if not scale:
        problems.append("baseline.json: severity_scale is empty")
    for b in baseline.get("bugs", []):
        if b.get("severity") not in scale:
            problems.append(f"baseline.json: {b.get('id')} severity {b.get('severity')!r} not in severity_scale")
    missing = REQUIRED_THRESHOLDS - set(baseline.get("thresholds", {}))
    if missing:
        problems.append(f"baseline.json: thresholds missing {sorted(missing)}")
    return problems


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile_dir", type=Path)
    ap.add_argument("--skill-name", required=True)
    ap.add_argument("--skill-version", default="final")
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--has-refinement", action="store_true",
                    help="trainee submitted a refined version (real L2)")
    ap.add_argument("--baseline", type=Path, help="answer key to use instead of <profile_dir>/baseline.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    cpath = args.profile_dir / "criteria.json"
    bpath = args.baseline or args.profile_dir / "baseline.json"
    criteria = json.loads(cpath.read_text(encoding="utf-8"))
    baseline = json.loads(bpath.read_text(encoding="utf-8"))

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
            "primary_axes": ["correctness"],
            "n_repeats": 1,
            "assessment": {
                "profile": args.profile_dir.name,
                "criteria_version": criteria.get("version"),
                "baseline_version": baseline.get("version"),
                "criteria_sha256": sha256(cpath),
                "baseline_sha256": sha256(bpath),
                "pass_threshold": criteria["pass_threshold"],
                "groups": criteria["groups"],
                "l0_override": criteria.get("l0_override"),
                "criteria": criteria["criteria"],
            },
        },
        "baseline": {
            "type": "assessment_baseline",
            "reference": f"profiles/{args.profile_dir.name}/baseline.json assessment "
                         f"{baseline['assessment_id']} v{baseline.get('version')}",
        },
        "evals": [{
            "id": 1,
            "name": baseline["assessment_id"],
            "prompt": f"See requirement source: {baseline['requirement_source']}",
            "files": [baseline["requirement_source"]],
            "assertions": [
                {"id": c["id"], "text": f"{c['name']}: {c['pass_when']}", "pre_registered": True}
                for c in criteria["criteria"]
            ],
            "exploratory_assertions": [],
        }],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(g["max_points"] for g in criteria["groups"])
    print(f"Wrote {args.out}: {len(criteria['criteria'])} criteria, {total} points, pass at {criteria['pass_threshold']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
