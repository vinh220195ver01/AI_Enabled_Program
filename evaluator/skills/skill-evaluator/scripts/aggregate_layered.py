#!/usr/bin/env python3
"""
Layered benchmark aggregator for skill-evaluator.

Reads per-run result.json files (schema: references/schemas.md, "Layer-tagged
run record") from a workspace directory structured as:

    <workspace>/<layer>/<eval_id>/run-<n>/result.json

and produces a layer-tagged benchmark.json (schema: references/schemas.md,
"Layer-tagged benchmark.json") with mean/stddev per layer x configuration x
axis, plus an L3 delta section if both L1 and L2 data are present.

This script is self-contained (stdlib only) and works whether or not
skill-creator is available in the environment. If skill-creator's
scripts/aggregate_benchmark.py IS available and you'd rather feed its
flat benchmark.json into an existing viewer per-layer, you can also just
call this script once per layer directory and keep the outputs separate --
see references/skill-creator-integration.md.

Usage:
    python -m scripts.aggregate_layered <workspace_dir> --skill-name <name>
"""

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List


def load_runs(layer_dir: Path) -> List[Dict[str, Any]]:
    runs = []
    if not layer_dir.exists():
        return runs
    for eval_dir in sorted(layer_dir.iterdir()):
        if not eval_dir.is_dir():
            continue
        for run_dir in sorted(eval_dir.glob("run-*")):
            result_path = run_dir / "result.json"
            if result_path.exists():
                with open(result_path) as f:
                    runs.append(json.load(f))
    return runs


def mean_stddev(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": None, "stddev": None, "n": 0}
    if len(values) == 1:
        return {"mean": values[0], "stddev": 0.0, "n": 1}
    return {
        "mean": round(statistics.mean(values), 4),
        "stddev": round(statistics.stdev(values), 4),
        "n": len(values),
    }


def summarize_configuration(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    correctness = [r["correctness"]["pass_rate"] for r in runs if "correctness" in r]
    quality = [r["quality"]["overall_score"] for r in runs if "quality" in r]
    tokens = [r["efficiency"]["tokens"] for r in runs if "efficiency" in r]
    duration = [r["efficiency"]["duration_seconds"] for r in runs if "efficiency" in r]

    return {
        "correctness": mean_stddev(correctness),
        "quality": mean_stddev(quality),
        "efficiency_tokens": mean_stddev(tokens),
        "efficiency_seconds": mean_stddev(duration),
    }


def summarize_layer(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_config: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        config = r.get("configuration", "with_skill")
        by_config.setdefault(config, []).append(r)
    return {config: summarize_configuration(rs) for config, rs in by_config.items()}


def compute_l3_delta(l1_summary: Dict[str, Any], l2_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Compare with_skill L1 vs with_skill L2 summaries, if both present."""
    l1 = l1_summary.get("with_skill")
    l2 = l2_summary.get("with_skill")
    if not l1 or not l2:
        return {}

    def delta_str(a, b):
        if a.get("mean") is None or b.get("mean") is None:
            return None
        d = b["mean"] - a["mean"]
        return f"{'+' if d >= 0 else ''}{round(d, 4)}"

    correctness_delta = delta_str(l1["correctness"], l2["correctness"])
    quality_delta = delta_str(l1["quality"], l2["quality"])
    token_delta = delta_str(l1["efficiency_tokens"], l2["efficiency_tokens"])

    return {
        "correctness_delta": correctness_delta,
        "quality_delta": quality_delta,
        "extra_cost_tokens": token_delta,
        # Verdict is deliberately left for agents/refinement-analyzer.md to
        # judge with reasoning -- this script reports the numbers, not the
        # substance-vs-polish or worth-it call, which needs to read the
        # actual output text to be meaningful.
        "note": "See agents/refinement-analyzer.md output for substance-vs-polish "
        "and worth-it judgments -- this script only aggregates the numbers.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--n-repeats", type=int, default=None)
    args = parser.parse_args()

    layers_present = [
        layer for layer in ("L1", "L2") if (args.workspace / layer).exists()
    ]

    run_summary = {}
    for layer in layers_present:
        runs = load_runs(args.workspace / layer)
        run_summary[layer] = summarize_layer(runs)

    l3_delta = {}
    if "L1" in run_summary and "L2" in run_summary:
        l3_delta = compute_l3_delta(run_summary["L1"], run_summary["L2"])

    benchmark = {
        "metadata": {
            "skill_name": args.skill_name,
            "layers_evaluated": layers_present,
            "n_repeats": args.n_repeats,
        },
        "run_summary": run_summary,
        "l3_delta": l3_delta,
        "notes": [],
    }

    out_path = args.workspace / "benchmark.json"
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2)

    print(f"Wrote {out_path}")
    print(json.dumps(benchmark, indent=2))


if __name__ == "__main__":
    main()
