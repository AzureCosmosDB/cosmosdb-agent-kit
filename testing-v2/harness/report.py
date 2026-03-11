"""
Utility for generating structured test reports that feed the evaluation loop.

After tests run, this produces a JSON report that the CI workflow and the
evaluating agent can use to:
1. Determine pass/fail counts per category
2. Identify which contract endpoints failed
3. Propose rule/skill improvements
"""

import json
import datetime
from pathlib import Path


def generate_test_report(
    scenario: str,
    iteration: str,
    language: str,
    pytest_json: dict,
    output_path: Path,
):
    """
    Transform pytest results into a structured evaluation report.

    Args:
        scenario: Scenario name (e.g., 'gaming-leaderboard')
        iteration: Iteration ID (e.g., 'iteration-004-python')
        language: Language used (e.g., 'python')
        pytest_json: Parsed pytest JSON output
        output_path: Where to write the report
    """
    tests = pytest_json.get("tests", [])

    # Categorize results
    categories = {}
    for test in tests:
        # Extract category from test node ID, e.g. test_api_contract.py::test_create_player
        nodeid = test.get("nodeid", "")
        if "test_api_contract" in nodeid:
            cat = "api_contract"
        elif "test_data_integrity" in nodeid:
            cat = "data_integrity"
        elif "test_best_practices" in nodeid:
            cat = "best_practices"
        else:
            cat = "other"

        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}

        outcome = test.get("outcome", "unknown")
        if outcome == "passed":
            categories[cat]["passed"] += 1
        elif outcome == "failed":
            categories[cat]["failed"] += 1
            categories[cat]["errors"].append({
                "test": nodeid,
                "message": _extract_failure_message(test),
            })
        else:
            categories[cat]["skipped"] += 1

    total_passed = sum(c["passed"] for c in categories.values())
    total_failed = sum(c["failed"] for c in categories.values())
    total_tests = total_passed + total_failed + sum(c["skipped"] for c in categories.values())

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scenario": scenario,
        "iteration": iteration,
        "language": language,
        "summary": {
            "total": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "pass_rate": round(total_passed / total_tests * 100, 1) if total_tests > 0 else 0,
        },
        "categories": categories,
        "failures_requiring_evaluation": [
            err
            for cat in categories.values()
            for err in cat["errors"]
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def format_report_as_markdown(report: dict) -> str:
    """Format a test report as a Markdown summary for PR comments."""
    s = report["summary"]
    lines = [
        f"## Test Results: {report['scenario']} / {report['iteration']}",
        "",
        f"**Language**: {report['language']}",
        f"**Pass rate**: {s['pass_rate']}% ({s['passed']}/{s['total']})",
        "",
        "| Category | Passed | Failed | Skipped |",
        "|----------|--------|--------|---------|",
    ]

    for cat_name, cat_data in report["categories"].items():
        lines.append(
            f"| {cat_name} | {cat_data['passed']} | {cat_data['failed']} | {cat_data['skipped']} |"
        )

    if report["failures_requiring_evaluation"]:
        lines.append("")
        lines.append("### Failures Requiring Evaluation")
        lines.append("")
        for failure in report["failures_requiring_evaluation"]:
            lines.append(f"- **{failure['test']}**: {failure['message'][:200]}")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated at {report['generated_at']}*")

    return "\n".join(lines)


def _extract_failure_message(test: dict) -> str:
    """Extract a readable failure message from pytest test result."""
    call = test.get("call", {})
    if isinstance(call, dict):
        longrepr = call.get("longrepr", "")
        if longrepr:
            # Take the last line which usually has the assertion message
            lines = str(longrepr).strip().split("\n")
            return lines[-1] if lines else "Unknown failure"
    return test.get("outcome", "Unknown failure")
