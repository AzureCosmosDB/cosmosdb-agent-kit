#!/usr/bin/env python3
"""
Aggregate test results from multiple batch iteration runs.

Computes mean, stddev, min, max pass rates and per-test consistency
analysis across N independent code generations of the same scenario.

Usage:
    python aggregate.py \
        --reports run-1/test-report.json run-2/test-report.json ... \
        --scenario ecommerce-order-api \
        --language python \
        --skills yes \
        --batch-issue 42 \
        --pr-numbers "51,52,53,54,55" \
        --output-md BATCH-RESULTS.md \
        --output-json batch-results.json
"""

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_reports(paths):
    """Load test-report.json files from the given paths."""
    reports = []
    for p in paths:
        path = Path(p)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            reports.append(data)
        else:
            print(f"WARNING: Report not found: {p}", file=sys.stderr)
    return reports


def compute_aggregate(reports):
    """Compute aggregate statistics from multiple test reports."""
    n = len(reports)
    if n == 0:
        return None

    # Extract per-run metrics
    pass_rates = []
    passed_counts = []
    failed_counts = []
    total_counts = []
    startup_failures = 0
    build_failures = 0
    build_startup_status = []  # per-iteration: {"build": bool, "startup": bool}

    for r in reports:
        summary = r.get("summary", {})

        # Determine build/startup status from signals or categories
        bs = r.get("build_signal")
        build_ok = bs.get("succeeded", True) if bs else True
        startup_ok = not (r.get("startup_failed") or r.get("app_startup_failed"))

        # Also check build_startup category for consistency
        bs_cat = r.get("categories", {}).get("build_startup", {})
        if bs_cat:
            build_test = next((t for t in r.get("tests", []) if t.get("name") == "build_startup::build_compilation"), None)
            startup_test = next((t for t in r.get("tests", []) if t.get("name") == "build_startup::app_startup"), None)
            if build_test:
                build_ok = build_test["outcome"] == "passed"
            if startup_test:
                startup_ok = startup_test["outcome"] == "passed"

        if not build_ok:
            build_failures += 1
        if not startup_ok:
            startup_failures += 1
        build_startup_status.append({"build": build_ok, "startup": startup_ok})

        if r.get("startup_failed") or r.get("app_startup_failed"):
            pass_rates.append(0.0)
            passed_counts.append(0)
            failed_counts.append(summary.get("total", 0))
            total_counts.append(summary.get("total", 0))
        else:
            pass_rates.append(summary.get("pass_rate", 0.0))
            passed_counts.append(summary.get("passed", 0))
            failed_counts.append(
                summary.get("failed", 0) + summary.get("errors", 0)
            )
            total_counts.append(summary.get("total", 0))

    # Per-test consistency analysis
    test_names = set()
    for r in reports:
        for t in r.get("tests", []):
            test_names.add(t["name"])

    test_consistency = {}
    for name in sorted(test_names):
        outcomes = []
        for r in reports:
            found = False
            for t in r.get("tests", []):
                if t["name"] == name:
                    outcomes.append(t["outcome"])
                    found = True
                    break
            if not found:
                outcomes.append("missing")

        pass_count = sum(1 for o in outcomes if o == "passed")
        fail_count = sum(1 for o in outcomes if o in ("failed", "error"))
        miss_count = sum(1 for o in outcomes if o == "missing")

        if pass_count == n:
            stability = "always-pass"
        elif fail_count + miss_count == n:
            stability = "always-fail"
        else:
            stability = "flaky"

        test_consistency[name] = {
            "outcomes": outcomes,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "miss_count": miss_count,
            "total_runs": n,
            "stability": stability,
            "pass_rate": round(pass_count / n * 100, 1),
        }

    # Compute score per run (same logic as evaluate.py)
    scores = []
    for r in reports:
        scores.append(compute_score(r))

    # Category-level analysis
    category_stats = {}
    all_categories = set()
    for r in reports:
        for cat in r.get("categories", {}):
            all_categories.add(cat)

    for cat in sorted(all_categories):
        cat_pass_rates = []
        for r in reports:
            cat_data = r.get("categories", {}).get(cat, {})
            cat_total = (
                cat_data.get("total", 0)
                or cat_data.get("passed", 0) + cat_data.get("failed", 0)
                + cat_data.get("errors", 0) + cat_data.get("skipped", 0)
            )
            cat_passed = cat_data.get("passed", 0)
            if cat_total > 0:
                cat_pass_rates.append(round(cat_passed / cat_total * 100, 1))
        if cat_pass_rates:
            category_stats[cat] = {
                "mean": round(statistics.mean(cat_pass_rates), 1),
                "stddev": round(statistics.stdev(cat_pass_rates), 1) if len(cat_pass_rates) > 1 else 0.0,
                "min": min(cat_pass_rates),
                "max": max(cat_pass_rates),
                "values": cat_pass_rates,
            }

    return {
        "iterations": n,
        "startup_failures": startup_failures,
        "build_failures": build_failures,
        "build_startup_status": build_startup_status,
        "pass_rate": {
            "mean": round(statistics.mean(pass_rates), 1),
            "stddev": round(statistics.stdev(pass_rates), 1) if n > 1 else 0.0,
            "min": round(min(pass_rates), 1),
            "max": round(max(pass_rates), 1),
            "values": pass_rates,
        },
        "score": {
            "mean": round(statistics.mean(scores), 1),
            "stddev": round(statistics.stdev(scores), 1) if n > 1 else 0.0,
            "min": min(scores),
            "max": max(scores),
            "values": scores,
        },
        "passed": {"mean": round(statistics.mean(passed_counts), 1), "values": passed_counts},
        "failed": {"mean": round(statistics.mean(failed_counts), 1), "values": failed_counts},
        "total": {"mean": round(statistics.mean(total_counts), 1), "values": total_counts},
        "test_consistency": test_consistency,
        "category_stats": category_stats,
    }


def compute_score(report):
    """Compute score from a single test report (mirrors evaluate.py logic)."""
    if report is None or report.get("startup_failed") or report.get("app_startup_failed"):
        return 1

    rate = report.get("summary", {}).get("pass_rate", 0)

    if rate == 100:
        base = 10
    elif rate >= 90:
        base = 9
    elif rate >= 80:
        base = 8
    elif rate >= 70:
        base = 7
    elif rate >= 60:
        base = 6
    elif rate >= 50:
        base = 5
    elif rate >= 40:
        base = 4
    elif rate >= 25:
        base = 3
    elif rate > 0:
        base = 2
    else:
        base = 1

    build_signal = report.get("build_signal")
    if build_signal and not build_signal.get("succeeded", True):
        base = max(1, base - 1)

    categories = report.get("categories", {})
    infra = categories.get("cosmos_infrastructure", {})
    infra_failures = infra.get("failed", 0) + infra.get("errors", 0)
    if infra_failures > 0:
        penalty = (infra_failures + 2) // 3
        base = max(1, base - penalty)

    return base


def format_markdown(aggregate, scenario, language, skills, batch_issue, pr_numbers):
    """Generate BATCH-RESULTS.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    skills_text = "Yes (skills loaded)" if skills == "yes" else "No (control run)"
    n = aggregate["iterations"]

    lines = []
    lines.append(f"# Batch Test Results: {scenario.replace('-', ' ').title()}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- **Date**: {now}")
    lines.append(f"- **Scenario**: {scenario}")
    lines.append(f"- **Language**: {language}")
    lines.append(f"- **Skills loaded**: {skills_text}")
    lines.append(f"- **Iterations**: {n}")
    lines.append(f"- **Batch issue**: #{batch_issue}")
    lines.append(f"- **Child PRs**: {pr_numbers}")
    if aggregate["build_failures"] > 0:
        lines.append(f"- **Build failures**: {aggregate['build_failures']}/{n}")
    if aggregate["startup_failures"] > 0:
        lines.append(f"- **Startup failures**: {aggregate['startup_failures']}/{n}")
    lines.append("")

    # Aggregate summary
    pr = aggregate["pass_rate"]
    sc = aggregate["score"]
    lines.append("## Aggregate Summary")
    lines.append("")
    lines.append("| Metric | Mean | Std Dev | Min | Max | Range |")
    lines.append("|--------|------|---------|-----|-----|-------|")
    lines.append(
        f"| Pass Rate | {pr['mean']}% | {pr['stddev']}% "
        f"| {pr['min']}% | {pr['max']}% | {pr['max'] - pr['min']}% |"
    )
    lines.append(
        f"| Score (1-10) | {sc['mean']} | {sc['stddev']} "
        f"| {sc['min']} | {sc['max']} | {sc['max'] - sc['min']} |"
    )
    lines.append("")

    # Per-iteration breakdown
    bs_status = aggregate.get("build_startup_status", [])
    lines.append("## Per-Iteration Results")
    lines.append("")
    lines.append("| Run | Build | Startup | Passed | Total | Pass Rate | Score |")
    lines.append("|-----|-------|---------|--------|-------|-----------|-------|")
    for i in range(n):
        p = aggregate["passed"]["values"][i]
        t = aggregate["total"]["values"][i]
        r = aggregate["pass_rate"]["values"][i]
        s = aggregate["score"]["values"][i]
        if i < len(bs_status):
            b_icon = "PASS" if bs_status[i]["build"] else "FAIL"
            s_icon = "PASS" if bs_status[i]["startup"] else "FAIL"
        else:
            b_icon = "?"
            s_icon = "?"
        lines.append(f"| {i + 1} | {b_icon} | {s_icon} | {p} | {t} | {r}% | {s}/10 |")
    lines.append("")

    # Category breakdown
    if aggregate["category_stats"]:
        cat_labels = {
            "build_startup": "Build & Startup",
            "api_contract": "API Contract",
            "data_integrity": "Data Integrity",
            "robustness": "Robustness",
            "cosmos_infrastructure": "Cosmos Infrastructure",
            "other": "Other",
        }
        lines.append("## Category Breakdown")
        lines.append("")
        lines.append("| Category | Mean | Std Dev | Min | Max |")
        lines.append("|----------|------|---------|-----|-----|")
        for cat, stats in sorted(aggregate["category_stats"].items()):
            label = cat_labels.get(cat, cat)
            lines.append(
                f"| {label} | {stats['mean']}% | {stats['stddev']}% "
                f"| {stats['min']}% | {stats['max']}% |"
            )
        lines.append("")

    # Test consistency
    tc = aggregate["test_consistency"]
    always_pass = {k: v for k, v in tc.items() if v["stability"] == "always-pass"}
    always_fail = {k: v for k, v in tc.items() if v["stability"] == "always-fail"}
    flaky = {k: v for k, v in tc.items() if v["stability"] == "flaky"}

    lines.append("## Test Consistency Analysis")
    lines.append("")
    lines.append(
        f"- **Always pass**: {len(always_pass)} tests "
        f"({round(len(always_pass) / max(len(tc), 1) * 100)}%)"
    )
    lines.append(
        f"- **Always fail**: {len(always_fail)} tests "
        f"({round(len(always_fail) / max(len(tc), 1) * 100)}%)"
    )
    lines.append(
        f"- **Flaky** (stochastic): {len(flaky)} tests "
        f"({round(len(flaky) / max(len(tc), 1) * 100)}%)"
    )
    lines.append("")

    if always_pass:
        lines.append(f"### Consistent Passes ({len(always_pass)} tests)")
        lines.append("")
        for name in sorted(always_pass.keys()):
            lines.append(f"- `{name}`")
        lines.append("")

    if always_fail:
        lines.append(f"### Consistent Failures ({len(always_fail)} tests)")
        lines.append("")
        lines.append(
            "These tests failed in EVERY iteration — likely indicates a real gap "
            "(missing rule, contract misunderstanding, or SDK issue)."
        )
        lines.append("")
        for name in sorted(always_fail.keys()):
            lines.append(f"- `{name}`")
        lines.append("")

    if flaky:
        lines.append(f"### Flaky Tests ({len(flaky)} tests)")
        lines.append("")
        lines.append(
            "These tests passed in some iterations but failed in others — "
            "indicates LLM stochasticity rather than a systematic gap."
        )
        lines.append("")
        lines.append("| Test | Pass Rate | Outcomes |")
        lines.append("|------|-----------|----------|")
        for name in sorted(flaky.keys()):
            v = flaky[name]
            outcomes_str = ", ".join(v["outcomes"])
            lines.append(f"| `{name}` | {v['pass_rate']}% | {outcomes_str} |")
        lines.append("")

    # Statistical significance assessment
    lines.append("## Statistical Assessment")
    lines.append("")
    if pr["stddev"] < 3:
        lines.append(
            "**High confidence** (σ < 3%): Results are highly consistent across "
            "iterations. Differences from other conditions are likely real, not noise."
        )
    elif pr["stddev"] < 8:
        lines.append(
            "**Moderate confidence** (3% ≤ σ < 8%): Some variance across iterations. "
            "Compare aggregate means to determine if differences are meaningful."
        )
    elif pr["stddev"] < 15:
        lines.append(
            "**Low confidence** (8% ≤ σ < 15%): Significant variance across iterations. "
            "Consider running more iterations for reliable comparison."
        )
    else:
        lines.append(
            "**Insufficient confidence** (σ ≥ 15%): Very high variance — results are "
            "dominated by LLM stochasticity. More iterations or scenario simplification needed."
        )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate batch test results")
    parser.add_argument(
        "--reports", nargs="+", required=True,
        help="Paths to test-report.json files",
    )
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--skills", required=True, choices=["yes", "no"])
    parser.add_argument("--batch-issue", required=True)
    parser.add_argument("--pr-numbers", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)

    args = parser.parse_args()

    reports = load_reports(args.reports)
    if not reports:
        print("ERROR: No reports loaded", file=sys.stderr)
        sys.exit(1)

    aggregate = compute_aggregate(reports)

    # Write markdown
    md = format_markdown(
        aggregate, args.scenario, args.language, args.skills,
        args.batch_issue, args.pr_numbers,
    )
    Path(args.output_md).write_text(md, encoding="utf-8")
    print(f"Wrote {args.output_md}")

    # Write JSON (for programmatic comparison of skills vs control)
    output = {
        "batch_issue": int(args.batch_issue),
        "scenario": args.scenario,
        "language": args.language,
        "skills": args.skills,
        "pr_numbers": args.pr_numbers,
        "aggregate": aggregate,
    }
    Path(args.output_json).write_text(
        json.dumps(output, indent=2), encoding="utf-8",
    )
    print(f"Wrote {args.output_json}")


if __name__ == "__main__":
    main()
