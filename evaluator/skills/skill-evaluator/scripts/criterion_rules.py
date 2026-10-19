#!/usr/bin/env python3
"""
Pass rules: how a criterion's verdict and score follow from its condition results.

The judge never decides a criterion's verdict. It reports, per condition, whether it is
met (with evidence). This module turns those results into a verdict and a score using
the criterion's `pass_rule`, so changing the rule (e.g. allowing a partial pass) is a data
change in one place: no judge prompt changes, and saved condition results can be
re-evaluated under the new rule without grading again.

Where the rule comes from (first one found wins):
    criterion.pass_rule  >  group.pass_rule  >  profile pass_rule
The course-wide default lives in profiles/_shared/course-rules.json (`settings.pass_rule`)
and reaches every profile through `extends` (see profile_loader.py).

Rule shape:
    {"mode": "all"}                                   every condition must be met
    {"mode": "at_least", "min_met": 5}                at least 5 conditions met
    {"mode": "at_least", "min_ratio": 0.8}            at least 80% of conditions met
    {"mode": "proportional", "min_ratio": 0.6}        score = met / total (partial
                                                      credit); verdict pass at >= 60%
  optional on any mode:
    "conditions": "pass_when_all" (default) | "should_items"   which list is counted
    "requires_pass_of": ["B3", "B5"]   the verdict is fail unless these criteria pass
    "text": "..."                      human-readable statement of the rule

Score: `all` and `at_least` give 1.0 for pass and 0.0 for fail; `proportional` gives
met / total. A failed `requires_pass_of` gives verdict fail and score 0.0.

Conditions counted for `pass_when_all`: the criterion's own `pass_when_all` followed by
`by_sub_category[<sub>].pass_when_all` when the criterion has sub-category variants
(the sub-category must then be given). Results are matched to conditions by position,
in that order.

Usage:
    python scripts/criterion_rules.py profiles/manual-qa profiles/auto-qa
        prints the effective rule of every criterion and where it comes from
    python scripts/criterion_rules.py profiles/auto-qa --results r.json [--sub-category SCR]
        r.json = {"A1": [true, false], "B1": [{"met": true, "evidence": "..."}], ...}
        prints verdict and score per criterion
"""
import argparse
import json
import sys
from pathlib import Path

MODES = {"all", "at_least", "proportional"}
CONDITION_SOURCES = {"pass_when_all", "should_items"}


def rule_for(profile, criterion):
    """Return (rule, origin) for a criterion of a resolved profile; origin says where it came from."""
    if criterion.get("pass_rule"):
        return criterion["pass_rule"], f"criterion {criterion['id']}"
    group = next((g for g in profile.get("groups", []) if g.get("id") == criterion.get("group")), {})
    if group.get("pass_rule"):
        return group["pass_rule"], f"group {group['id']}"
    if profile.get("pass_rule"):
        return profile["pass_rule"], profile.get("settings_from", {}).get("pass_rule", "profile")
    return None, None


def conditions_for(criterion, rule, sub_category=None):
    """The list of conditions the rule counts, in the order results must be given."""
    source = rule.get("conditions", "pass_when_all")
    if source == "should_items":
        return list(criterion.get("should_items", []))
    conditions = list(criterion.get("pass_when_all", []))
    variants = criterion.get("by_sub_category")
    if variants:
        if sub_category is None:
            raise ValueError(f"{criterion['id']} has sub-category conditions; give the sub-category being assessed")
        if sub_category not in variants:
            raise ValueError(f"{criterion['id']}: unknown sub-category {sub_category!r}")
        conditions += variants[sub_category].get("pass_when_all", [])
    return conditions


def check_rule(rule, label):
    problems = []
    if not isinstance(rule, dict):
        return [f"{label}: pass_rule must be an object with a mode, got {type(rule).__name__}"]
    mode = rule.get("mode")
    if mode not in MODES:
        return [f"{label}: pass_rule mode {mode!r} is not one of {sorted(MODES)}"]
    has_met, has_ratio = "min_met" in rule, "min_ratio" in rule
    if mode == "at_least" and has_met == has_ratio:
        problems.append(f"{label}: at_least needs exactly one of min_met or min_ratio")
    if mode == "proportional" and not has_ratio:
        problems.append(f"{label}: proportional needs min_ratio (the pass line)")
    if mode == "all" and (has_met or has_ratio):
        problems.append(f"{label}: mode all takes no min_met or min_ratio")
    if has_met and not (isinstance(rule["min_met"], int) and rule["min_met"] >= 1):
        problems.append(f"{label}: min_met must be a whole number >= 1")
    if has_ratio and not (isinstance(rule["min_ratio"], (int, float)) and 0 < rule["min_ratio"] <= 1):
        problems.append(f"{label}: min_ratio must be > 0 and <= 1")
    if rule.get("conditions", "pass_when_all") not in CONDITION_SOURCES:
        problems.append(f"{label}: conditions must be one of {sorted(CONDITION_SOURCES)}")
    return problems


def check_rules(profile):
    """Every problem with the pass rules of a resolved profile (empty list when fine)."""
    problems = []
    if profile.get("pass_rule"):
        problems += check_rule(profile["pass_rule"], "profile")
    for g in profile.get("groups", []):
        if g.get("pass_rule"):
            problems += check_rule(g["pass_rule"], f"group {g.get('id')}")
    ids = {c.get("id") for c in profile.get("criteria", [])}
    for c in profile.get("criteria", []):
        rule, origin = rule_for(profile, c)
        if rule is None:
            problems.append(f"{c.get('id')}: no pass_rule on the criterion, its group or the profile")
            continue
        if origin.startswith("criterion"):
            problems += check_rule(rule, c["id"])
        if not isinstance(rule, dict):
            continue
        source = rule.get("conditions", "pass_when_all")
        if source == "should_items" and not c.get("should_items"):
            problems.append(f"{c['id']}: rule counts should_items but the criterion has none")
        if source == "pass_when_all" and not c.get("pass_when_all") and not any(
                v.get("pass_when_all") for v in c.get("by_sub_category", {}).values()):
            problems.append(f"{c['id']}: rule counts pass_when_all but the criterion has no conditions")
        if "min_met" in rule and source == "should_items" and rule["min_met"] > len(c.get("should_items", [])):
            problems.append(f"{c['id']}: min_met {rule['min_met']} is more than its {len(c['should_items'])} should_items")
        for dep in rule.get("requires_pass_of", []):
            if dep not in ids:
                problems.append(f"{c['id']}: requires_pass_of names unknown criterion {dep!r}")
            elif dep == c["id"]:
                problems.append(f"{c['id']}: requires_pass_of names itself")
    return problems


def evaluate(rule, results, upstream=None):
    """Verdict and score for one criterion.

    results: one entry per condition, a bool or a dict with "met".
    upstream: {criterion_id: verdict} for the ids in requires_pass_of.
    """
    met_flags = [r["met"] if isinstance(r, dict) else bool(r) for r in results]
    total, met = len(met_flags), sum(met_flags)
    ratio = met / total if total else 0.0
    mode = rule["mode"]
    if mode == "all":
        passed, score = met == total and total > 0, None
    elif mode == "at_least":
        passed = met >= rule["min_met"] if "min_met" in rule else ratio >= rule["min_ratio"]
        score = None
    else:
        passed, score = ratio >= rule["min_ratio"], ratio
    blocked = [d for d in rule.get("requires_pass_of", []) if (upstream or {}).get(d) != "pass"]
    if blocked:
        passed, score = False, 0.0
    if score is None:
        score = 1.0 if passed else 0.0
    return {"verdict": "pass" if passed else "fail", "score": round(score, 4), "met": met, "total": total,
            "blocked_by": blocked}


def evaluate_all(profile, results, sub_category=None):
    """Evaluate every criterion that has results, dependencies first. Returns {id: outcome}."""
    by_id = {c["id"]: c for c in profile["criteria"]}
    outcomes, visiting = {}, set()

    def visit(cid):
        if cid in outcomes:
            return
        if cid in visiting:
            raise ValueError(f"requires_pass_of cycle at {cid}")
        visiting.add(cid)
        c = by_id[cid]
        rule, origin = rule_for(profile, c)
        for dep in rule.get("requires_pass_of", []):
            if dep in results:
                visit(dep)
        conditions = conditions_for(c, rule, sub_category)
        if len(results[cid]) != len(conditions):
            raise ValueError(f"{cid}: {len(results[cid])} results for {len(conditions)} conditions")
        upstream = {d: outcomes[d]["verdict"] for d in rule.get("requires_pass_of", []) if d in outcomes}
        outcomes[cid] = {**evaluate(rule, results[cid], upstream), "rule_origin": origin}
        visiting.discard(cid)

    for cid in results:
        if cid not in by_id:
            raise ValueError(f"results name unknown criterion {cid!r}")
        visit(cid)
    return outcomes


def main():
    from profile_loader import ProfileError, load_profile

    ap = argparse.ArgumentParser()
    ap.add_argument("profile_dirs", type=Path, nargs="+")
    ap.add_argument("--results", type=Path, help="condition results to evaluate (one profile only)")
    ap.add_argument("--sub-category", help="sub-category being assessed, for criteria with variants")
    args = ap.parse_args()
    if args.results and len(args.profile_dirs) != 1:
        ap.error("--results needs exactly one profile")

    for d in args.profile_dirs:
        try:
            profile, _ = load_profile(d)
        except ProfileError as e:
            print(f"{d}: {len(e.problems)} problem(s)")
            for p in e.problems:
                print(f"  - {p}")
            return 1
        if args.results:
            results = json.loads(args.results.read_text(encoding="utf-8"))
            try:
                outcomes = evaluate_all(profile, results, args.sub_category)
            except ValueError as e:
                print(f"{d}: {e}")
                return 1
            for cid, o in outcomes.items():
                blocked = f", blocked by {o['blocked_by']}" if o["blocked_by"] else ""
                print(f"{cid}: {o['verdict']} score {o['score']} ({o['met']}/{o['total']} met{blocked}; rule from {o['rule_origin']})")
            continue
        print(f"{d}:")
        for c in profile["criteria"]:
            rule, origin = rule_for(profile, c)
            shown = {k: v for k, v in rule.items() if k != "text"}
            print(f"  {c['id']}: {json.dumps(shown)}  <- {origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
