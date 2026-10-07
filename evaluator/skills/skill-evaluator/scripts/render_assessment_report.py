#!/usr/bin/env python3
"""
Combines the three score sources of a profile-based assessment into one report
with a single overall score, while keeping every part visible.

Inputs (all produced by the normal workflow):
  --plan    evals/eval_plan.json          (from build_plan_from_profile.py; carries
                                           weights, overrides, critical flags, gate_min)
  --l0      evals/l0_scores.json          (agents/input-layer-judge.md; the
                                           `dimensions` scores are the FINAL ones,
                                           i.e. already scored under any override)
  --result  <run>/result.json             (agents/manual-qa-assessment-judge.md)

Parts, each normalised to 0-100:
  general_l0  weighted mean of D1-D8 / 5      (override weights from the plan, default 1)
  rubric      weighted mean of rubric scores / 5
  coverage    passed / gradeable over scn:* and vp:* assertions
  checks      passed / gradeable over chk:* assertions

Gates (decided by the profile, never by the grader or by this script's caller):
  - a critical scn/vp assertion that failed  -> the whole `coverage` part is 0
  - a critical chk assertion that failed     -> the whole `checks` part is 0
  - a rubric dimension below its gate_min    -> that dimension contributes 0
  Gates never zero the other parts, only the criterion they belong to.
  A critical assertion graded null is reported as unresolved, not gated.

overall = sum(part * weight) / sum(weights of parts with weight > 0).
A part with weight > 0 and no data is an error, not a silent zero.

Usage:
    python scripts/render_assessment_report.py --plan evals/eval_plan.json \
        --l0 evals/l0_scores.json --result L1/1/run-1/result.json --out-dir report/
"""
import argparse
import json
import sys
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pct(num, den):
    return None if not den else round(100.0 * num / den, 2)


def part_general(plan, l0, notes):
    overrides = {o["dimension"]: o for o in plan["scope"]["assessment"]["l0_overrides"]}
    scored = l0["dimensions"]
    rows, tot, wsum = [], 0.0, 0.0
    for key, d in sorted(scored.items()):
        code = key.split("_")[0].upper()
        o = overrides.get(code)
        w = o["weight"] if o and o["change"] == "weight" else 1.0
        rows.append({"dimension": code, "score": d["score"], "weight": w,
                     "overridden": bool(o), "override_change": o["change"] if o else None})
        tot += d["score"] * w
        wsum += w
    applied = {a["dimension"]: a for a in l0.get("overrides_applied", [])}
    for code, o in overrides.items():
        if o["change"] == "anchors" and code not in applied:
            notes.append(f"override on {code} changes anchors but l0_scores.json has no "
                         f"overrides_applied entry for it -- the L0 judge did not record default vs final.")
        if code in applied:
            for r in rows:
                if r["dimension"] == code:
                    r["default_score"] = applied[code].get("default_score")
    return pct(tot, 5 * wsum), rows


def part_assertions(plan, result, prefixes, gate_label, notes):
    plan_asserts = {a["id"]: a for a in plan["evals"][0]["assertions"] if a["id"].split(":")[0] in prefixes}
    graded = {e["id"]: e for e in result["correctness"]["expectations"] if e["id"] in plan_asserts}
    missing = sorted(set(plan_asserts) - set(graded))
    if missing:
        notes.append(f"{gate_label}: no verdict recorded for {missing}")
    gradeable = [i for i, e in graded.items() if e["passed"] is not None]
    passed = [i for i in gradeable if graded[i]["passed"]]
    failed_critical = [i for i in gradeable if not graded[i]["passed"] and plan_asserts[i].get("critical")]
    unresolved = [i for i, e in graded.items() if e["passed"] is None and plan_asserts[i].get("critical")]
    if unresolved:
        notes.append(f"{gate_label}: critical assertion(s) graded null, not gated: {unresolved}")
    raw = pct(len(passed), len(gradeable))
    score = 0.0 if failed_critical else raw
    return score, {"raw": raw, "passed": len(passed), "gradeable": len(gradeable),
                   "gated_by": failed_critical,
                   "missed": sorted(i for i in gradeable if i not in passed)}


def part_rubric(plan, result):
    dims = plan["scope"]["quality_rubric"]["dimensions"]
    scores = result["quality"]["rubric"]
    rows, tot, wsum, gated = [], 0.0, 0.0, []
    for name, d in dims.items():
        if name not in scores:
            raise ValueError(f"result.json quality.rubric has no score for '{name}'")
        s, w = scores[name], d["weight"]
        gate = d.get("gate_min")
        hit = gate is not None and s < gate
        if hit:
            gated.append(name)
        rows.append({"dimension": name, "score": s, "weight": w, "gate_min": gate, "gated": hit})
        tot += (0 if hit else s) * w
        wsum += w
    return pct(tot, 5 * wsum), {"rows": rows, "gated": gated}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--l0", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--out-dir", required=True, type=Path)
    a = ap.parse_args()

    plan, l0, result = load(a.plan), load(a.l0), load(a.result)
    weights = plan["scope"]["assessment"]["overall_weights"]
    notes, parts, detail = [], {}, {}

    parts["general_l0"], detail["general_l0"] = part_general(plan, l0, notes)
    parts["rubric"], detail["rubric"] = part_rubric(plan, result)
    parts["coverage"], detail["coverage"] = part_assertions(plan, result, {"scn", "vp"}, "coverage", notes)
    parts["checks"], detail["checks"] = part_assertions(plan, result, {"chk"}, "checks", notes)

    active = {k: w for k, w in weights.items() if w > 0}
    for k in active:
        if parts[k] is None:
            print(f"error: part '{k}' has weight {active[k]} but no data to score it", file=sys.stderr)
            return 1
    overall = round(sum(parts[k] * w for k, w in active.items()) / sum(active.values()), 2)

    report = {"overall_score": overall, "parts": parts, "weights": weights, "detail": detail, "notes": notes}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / "assessment_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [f"# Assessment report: {plan['skill_name']}", "",
          f"**Overall: {overall} / 100**", "",
          "| Part | Weight | Score (0-100) | Notes |", "|---|---|---|---|"]
    for k in ("general_l0", "rubric", "coverage", "checks"):
        extra = ""
        if k in ("coverage", "checks") and detail[k]["gated_by"]:
            extra = f"GATED to 0 by critical miss: {detail[k]['gated_by']} (raw {detail[k]['raw']})"
        if k == "rubric" and detail[k]["gated"]:
            extra = f"gated dimensions contribute 0: {detail[k]['gated']}"
        md.append(f"| {k} | {weights[k]} | {parts[k]} | {extra} |")
    md += ["", "## A. General skill-evaluator dimensions (D1-D8, final scores)", "",
           "| Dim | Final | Default | Weight | Overridden |", "|---|---|---|---|---|"]
    for r in detail["general_l0"]:
        md.append(f"| {r['dimension']} | {r['score']} | {r.get('default_score', '-')} | {r['weight']} | {'yes: ' + r['override_change'] if r['overridden'] else 'no'} |")
    md += ["", "## B. Manual QA rubric and checks", "", "| Criterion | Score | Weight | Gate |", "|---|---|---|---|"]
    for r in detail["rubric"]["rows"]:
        md.append(f"| {r['dimension']} | {r['score']} | {r['weight']} | {'FAILED (min ' + str(r['gate_min']) + ')' if r['gated'] else '-'} |")
    md += ["", f"Coverage: {detail['coverage']['passed']}/{detail['coverage']['gradeable']} passed; missed: {detail['coverage']['missed']}",
           f"Checks: {detail['checks']['passed']}/{detail['checks']['gradeable']} passed; missed: {detail['checks']['missed']}"]
    if notes:
        md += ["", "## Notes"] + [f"- {n}" for n in notes]
    (a.out_dir / "assessment_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"overall={overall}  parts={parts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
