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


# ---------------------------------------------------------------------------
# CLI entry point — used by CI to parse JUnit XML and produce reports
# ---------------------------------------------------------------------------

def _cli_main():
    """
    Parse test-results.xml (JUnit XML) and write test-report.md + test-report.json.

    Expected environment variables:
        SCENARIO       — scenario name
        ITERATION      — iteration id
        ITERATION_DIR  — path to iteration directory (for reading app-output.log)
    """
    import xml.etree.ElementTree as ET
    import os
    import sys

    # Prevent UnicodeEncodeError for emoji on Windows CI runners
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    scenario = os.environ.get("SCENARIO", "unknown")
    iteration = os.environ.get("ITERATION", "unknown")
    iteration_dir = os.environ.get("ITERATION_DIR", "")

    # If test-results.xml doesn't exist, the app likely failed to start
    if not Path("test-results.xml").exists():
        app_log = ""
        app_err = ""
        if iteration_dir:
            log_path = Path(iteration_dir) / "app-output.log"
            err_path = Path(iteration_dir) / "app-error.log"
            if log_path.exists():
                app_log = log_path.read_text(errors="replace")[-3000:]
            if err_path.exists():
                app_err = err_path.read_text(errors="replace")[-3000:]

        lines = [
            f"## [Test] Test Results: {scenario} / {iteration}",
            "",
            "**Pass rate: N/A** -- application failed to start, no tests ran",
            "",
            "### [FAIL] Application Failed to Start",
            "",
            "The application did not start successfully, so no tests could run.",
            "This typically means a missing dependency, import error, or configuration issue.",
            "",
        ]

        if app_log:
            lines.extend([
                "<details>",
                "<summary>Application stdout (last 3000 chars)</summary>",
                "",
                "```",
                app_log,
                "```",
                "",
                "</details>",
                "",
            ])

        if app_err:
            lines.extend([
                "<details>",
                "<summary>Application stderr (last 3000 chars)</summary>",
                "",
                "```",
                app_err,
                "```",
                "",
                "</details>",
                "",
            ])

        report_md = "\n".join(lines)
        Path("test-report.md").write_text(report_md, encoding="utf-8")

        report_json = {
            "scenario": scenario,
            "iteration": iteration,
            "summary": {
                "total": 0, "passed": 0, "failed": 0,
                "errors": 1, "skipped": 0, "pass_rate": 0,
            },
            "failures": [{
                "test": "startup",
                "message": "Application failed to start. "
                           + (app_err[-500:] if app_err else (app_log[-500:] if app_log else "No output captured.")),
            }],
            "startup_failed": True,
        }
        Path("test-report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")

        print(report_md)
        return

    # Normal path: parse JUnit XML test results
    tree = ET.parse("test-results.xml")
    root = tree.getroot()

    suite = root.find(".//testsuite") or root
    total = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failures - errors - skipped
    pass_rate = round(passed / total * 100, 1) if total > 0 else 0

    # --- Categorize test results by file for better signal reporting ---
    category_counts = {}
    all_tests = []
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        failure = tc.find("failure")
        error = tc.find("error")
        skipped_el = tc.find("skipped")

        # Determine category from classname or test file
        if "cosmos_infrastructure" in classname or "cosmos_infrastructure" in name:
            cat = "cosmos_infrastructure"
        elif "data_integrity" in classname:
            cat = "data_integrity"
        elif "robustness" in classname:
            cat = "robustness"
        elif "api_contract" in classname:
            cat = "api_contract"
        else:
            cat = "other"

        if cat not in category_counts:
            category_counts[cat] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}

        if failure is not None:
            category_counts[cat]["failed"] += 1
            outcome = "failed"
        elif error is not None:
            category_counts[cat]["errors"] += 1
            outcome = "error"
        elif skipped_el is not None:
            category_counts[cat]["skipped"] += 1
            outcome = "skipped"
        else:
            category_counts[cat]["passed"] += 1
            outcome = "passed"

        all_tests.append({"name": f"{classname}::{name}", "outcome": outcome, "category": cat})

    # --- Load build signal if available ---
    build_signal = None
    for signal_path in [
        Path("build-signal.json"),
        Path(iteration_dir) / "build-signal.json" if iteration_dir else None,
    ]:
        if signal_path and signal_path.exists():
            try:
                build_signal = json.loads(signal_path.read_text(errors="replace"))
            except Exception:
                pass
            break

    # --- Load startup signal if available ---
    startup_signal = None
    signal_path = Path("startup-signal.json")
    if signal_path.exists():
        try:
            startup_signal = json.loads(signal_path.read_text(errors="replace"))
        except Exception:
            pass

    lines = [
        f"## [Test] Test Results: {scenario} / {iteration}",
        "",
        f"**Pass rate: {pass_rate}%** ({passed}/{total} tests passed)",
        "",
    ]

    # --- Build/Startup Signal Section ---
    if build_signal or startup_signal:
        lines.extend([
            "### Build & Startup Signals",
            "",
        ])
        if build_signal:
            build_ok = build_signal.get("succeeded", True)
            lines.append(f"- **Build**: {'PASS' if build_ok else 'FAIL'} (exit code: {build_signal.get('exit_code', '?')})")
            if not build_ok:
                stderr = build_signal.get("stderr_tail", "")
                if stderr:
                    lines.extend([
                        "  <details>",
                        "  <summary>Build error output</summary>",
                        "",
                        "  ```",
                        f"  {stderr[:1000]}",
                        "  ```",
                        "",
                        "  </details>",
                    ])
        if startup_signal:
            start_ok = startup_signal.get("startup_succeeded", True)
            lines.append(f"- **Startup**: {'PASS' if start_ok else 'FAIL'}")
        lines.append("")

    # --- Test Results Table ---
    lines.extend([
        "| Status | Count |",
        "|--------|-------|",
        f"| [PASS] Passed | {passed} |",
        f"| [FAIL] Failed | {failures} |",
        f"| [ERR] Errors | {errors} |",
        f"| [SKIP] Skipped | {skipped} |",
        "",
    ])

    # --- Category Breakdown ---
    if category_counts:
        cat_labels = {
            "api_contract": "API Contract",
            "data_integrity": "Data Integrity",
            "robustness": "Robustness",
            "cosmos_infrastructure": "Cosmos DB Infrastructure & SDK",
            "other": "Other",
        }
        lines.extend([
            "### Results by Category",
            "",
            "| Category | Passed | Failed | Skipped |",
            "|----------|--------|--------|---------|",
        ])
        for cat, counts in sorted(category_counts.items()):
            label = cat_labels.get(cat, cat)
            f_count = counts["failed"] + counts["errors"]
            lines.append(f"| {label} | {counts['passed']} | {f_count} | {counts['skipped']} |")
        lines.append("")

    failure_details = []
    for tc in root.iter("testcase"):
        failure = tc.find("failure")
        error = tc.find("error")
        if failure is not None or error is not None:
            name = tc.get("name", "unknown")
            classname = tc.get("classname", "")
            msg = (failure if failure is not None else error).get("message", "")[:300]
            failure_details.append({"test": f"{classname}::{name}", "message": msg})

    if failure_details:
        lines.append("### Failures Requiring Evaluation")
        lines.append("")
        lines.append("These failures indicate areas where the generated code does not")
        lines.append("conform to the API contract or Cosmos DB best practices.")
        lines.append("Each failure should be analyzed to determine if:")
        lines.append("- A **new rule/skill** should be added to the agent kit")
        lines.append("- An **existing rule** needs to be updated or clarified")
        lines.append("- The **generated code** has a bug that the agent should fix")
        lines.append("")
        for f in failure_details:
            lines.append(f"- **{f['test']}**")
            lines.append(f"  > {f['message']}")
            lines.append("")

    if pass_rate == 100:
        lines.append("### [PASS] All tests passed!")
        lines.append("")
        lines.append("The generated application fully conforms to the API contract.")
        lines.append("Review the code for Cosmos DB best practices and merge if satisfactory.")

    report_md = "\n".join(lines)
    Path("test-report.md").write_text(report_md, encoding="utf-8")

    report_json = {
        "scenario": scenario,
        "iteration": iteration,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": pass_rate,
        },
        "categories": category_counts,
        "tests": all_tests,
        "build_signal": build_signal,
        "startup_signal": startup_signal,
        "failures": failure_details,
    }
    Path("test-report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    print(report_md)


if __name__ == "__main__":
    _cli_main()
