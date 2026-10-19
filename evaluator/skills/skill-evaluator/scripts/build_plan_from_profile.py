#!/usr/bin/env python3
"""
Turns a profile's criteria (profiles/<name>/criteria.json) plus ONE assessment's answer key
(--baseline PATH, different for every exam) into the pre-registered evals/eval_plan.json
(SKILL.md Step 1).

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

The profile is read with profile_loader.load_profile, which resolves shared criteria
fragments (`$ref` in groups, e.g. profiles/_shared/skill-standard.json). It records sha256
of criteria.json, of every shared fragment and of the answer key in the plan, so a later
edit to any of them after grading started is detectable.

Usage:
    python scripts/build_plan_from_profile.py profiles/manual-qa \
        --skill-name trainee-01 --hypothesis "..." --out evals/eval_plan.json

--baseline is required. The answer key belongs to one assessment and lives next to its
exam, not in the profile folder; profiles/<name>/baseline.template.json shows its shape.
"""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from profile_loader import ProfileError, load_profile

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
    model = criteria.get("scoring_model", "deduction")
    if model != "deduction":
        return [f"criteria.json: scoring_model {model!r} is not supported yet; this script only builds "
                f"plans for the 'deduction' points model ({criteria.get('status', 'no status given')})"]
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

    na = baseline.get("not_assessed", [])
    crit_ids = {c.get("id") for c in criteria.get("criteria", [])}
    na_ids = {x.get("criterion") for x in na}
    for x in na:
        if x.get("criterion") not in crit_ids:
            problems.append(f"baseline.json: not_assessed names unknown criterion {x.get('criterion')!r}")
        if not x.get("reason"):
            problems.append(f"baseline.json: not_assessed {x.get('criterion')} needs a reason")
    if na_ids >= crit_ids:
        problems.append("baseline.json: not_assessed removes every criterion")
    # a list is only required when an assessed criterion needs it
    needed = {"acceptance_criteria", "ambiguities", "edge_cases"}
    for c in criteria.get("criteria", []):
        if c.get("id") not in na_ids:
            needed |= set(c.get("needs", []))
    for key in ("acceptance_criteria", "ambiguities", "edge_cases", "bugs"):
        problems += dup_ids(baseline.get(key, []), f"baseline.json {key}")
        if key in needed and not baseline.get(key):
            problems.append(f"baseline.json: {key} is empty (needed by an assessed criterion; list the criterion under not_assessed if the exam does not cover it)")
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
    ap.add_argument("--baseline", type=Path, required=True, help="this assessment's answer key (baseline.json)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    cpath = args.profile_dir / "criteria.json"
    bpath = args.baseline
    try:
        criteria, sources = load_profile(args.profile_dir)
    except ProfileError as e:
        print(f"build_plan_from_profile: {len(e.problems)} problem(s), nothing written:\n")
        for p in e.problems:
            print(f"  - {p}")
        return 1
    baseline = json.loads(bpath.read_text(encoding="utf-8"))

    problems = validate(criteria, baseline)
    if baseline.get("profile") != args.profile_dir.name:
        problems.append(f"baseline.json: profile is {baseline.get('profile')!r}, expected {args.profile_dir.name!r}")
    if problems:
        print(f"build_plan_from_profile: {len(problems)} problem(s), nothing written:\n")
        for p in problems:
            print(f"  - {p}")
        return 1

    na_ids = {x["criterion"] for x in baseline.get("not_assessed", [])}
    full_total = sum(g["max_points"] for g in criteria["groups"])
    assessed = [c for c in criteria["criteria"] if c["id"] not in na_ids]
    groups = [{**g, "max_points": sum(c["max_points"] for c in assessed if c["group"] == g["id"])} for g in criteria["groups"]]
    assessed_total = sum(g["max_points"] for g in groups)
    # Assumption, flagged in the report: when criteria are not assessed, the pass line keeps the
    # same proportion of the points that remain (rounded up).
    threshold = math.ceil(criteria["pass_threshold"] * assessed_total / full_total) if na_ids else criteria["pass_threshold"]

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
                "shared_sources": sources[1:],
                "baseline_sha256": sha256(bpath),
                "pass_threshold": threshold,
                "pass_threshold_original": criteria["pass_threshold"],
                "full_total": full_total,
                "not_assessed": baseline.get("not_assessed", []),
                "groups": groups,
                "l0_override": criteria.get("l0_override"),
                "criteria": assessed,
            },
        },
        "baseline": {
            "type": "assessment_baseline",
            "reference": f"{args.baseline} assessment "
                         f"{baseline['assessment_id']} v{baseline.get('version')}",
        },
        "evals": [{
            "id": 1,
            "name": baseline["assessment_id"],
            "prompt": f"See requirement source: {baseline['requirement_source']}",
            "files": [baseline["requirement_source"]],
            "assertions": [
                {"id": c["id"], "text": f"{c['name']}: {c['pass_when']}", "pre_registered": True}
                for c in assessed
            ],
            "exploratory_assertions": [],
        }],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}: {len(assessed)} criteria, {assessed_total} points, pass at {threshold}")
    if na_ids:
        print(f"  not assessed: {sorted(na_ids)}; pass line scaled from {criteria['pass_threshold']}/{full_total} to {threshold}/{assessed_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
