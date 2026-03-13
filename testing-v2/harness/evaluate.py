#!/usr/bin/env python3
"""
Automated evaluation of test iteration results.

Creates ITERATION.md in the iteration directory and updates
testing-v2/IMPROVEMENTS-LOG.md with the test results.

Environment variables (set by CI):
    SCENARIO       - scenario name (e.g., gaming-leaderboard)
    ITERATION      - iteration id (e.g., iteration-001-python)
    ITERATION_DIR  - path to iteration directory

Reads:
    test-report.json (current directory, created by report.py)

Writes:
    {ITERATION_DIR}/ITERATION.md
    testing-v2/IMPROVEMENTS-LOG.md (append or replace entry)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_test_results():
    """Load test-report.json from the current directory."""
    path = Path("test-report.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_source_files(iteration_dir):
    """List source files in the iteration directory (excludes metadata/temp files)."""
    exclude = {
        "ITERATION.md", "iteration-config.yaml", "source-code.zip",
        "app-output.log", "app-error.log", "_start-app.cmd",
    }
    files = []
    root = Path(iteration_dir)
    if root.exists():
        for f in sorted(root.rglob("*")):
            if f.is_file() and f.name not in exclude:
                files.append(str(f.relative_to(root)))
    return files


def scan_code_patterns(iteration_dir):
    """Scan source code for known Cosmos DB patterns using regex."""
    checks = [
        ("singleton_client", r"cosmos.?client|CosmosClient"),
        ("direct_mode", r"direct.{0,20}(connection|mode)|ConnectionMode\.Direct"),
        ("gateway_mode", r"gateway.{0,20}(connection|mode)|ConnectionMode\.Gateway"),
        ("partition_key", r"partition.?key|PartitionKey"),
        ("bulk_operations", r"bulk|AllowBulkExecution"),
        ("etag_concurrency", r"etag|if.match|IfMatch"),
        ("point_reads", r"read.item|ReadItem|point.read"),
        ("cross_partition", r"cross.partition|enable_cross_partition"),
        ("indexing_policy", r"indexing.?policy|IndexingPolicy"),
        ("throughput", r"throughput|offer_throughput|setThroughput"),
        ("change_feed", r"change.?feed|ChangeFeed"),
        ("diagnostics", r"diagnostics|CosmosDiagnostics"),
    ]

    code_exts = {".py", ".cs", ".java", ".js", ".ts", ".go", ".rs"}
    all_code = []
    for f in Path(iteration_dir).rglob("*"):
        if f.is_file() and f.suffix in code_exts:
            try:
                all_code.append(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                pass

    combined = "\n".join(all_code)
    results = {}
    for name, pattern in checks:
        results[name] = bool(re.search(pattern, combined, re.IGNORECASE))
    return results


def compute_score(report):
    """Map pass rate to a 1-10 score."""
    if report is None or report.get("startup_failed"):
        return 1
    rate = report.get("summary", {}).get("pass_rate", 0)
    if rate == 100:
        return 10
    if rate >= 90:
        return 9
    if rate >= 80:
        return 8
    if rate >= 70:
        return 7
    if rate >= 60:
        return 6
    if rate >= 50:
        return 5
    if rate >= 40:
        return 4
    if rate >= 25:
        return 3
    if rate > 0:
        return 2
    return 1


def generate_iteration_md(scenario, iteration, report, patterns, source_files):
    """Generate ITERATION.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = report.get("summary", {}) if report else {}
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    errors = summary.get("errors", 0)
    skipped = summary.get("skipped", 0)
    pass_rate = summary.get("pass_rate", 0)
    score = compute_score(report)

    language = iteration.rsplit("-", 1)[-1] if "-" in iteration else "unknown"
    scenario_title = scenario.replace("-", " ").title()

    if pass_rate == 100:
        result_text = f"All {total} tests passed"
    else:
        result_text = f"{passed}/{total} tests passed ({pass_rate}%)"

    lines = [
        f"# {iteration} - {language.title()} {scenario_title}",
        "",
        "## Metadata",
        f"- **Date**: {now}",
        f"- **Language/SDK**: {language.title()}",
        f"- **Agent**: GitHub Copilot (automated iteration)",
        f"- **Tester**: Automated CI",
        "",
        "## Skills Verification",
        "",
        "**Were skills loaded before building?** Yes (via issue prompt referencing AGENTS.md)",
        "",
        "## Cosmos DB Patterns Detected",
        "",
        "| Pattern | Status | Related Rule |",
        "|---------|--------|--------------|",
    ]

    pattern_labels = [
        ("singleton_client", "Singleton CosmosClient", "sdk-singleton-client"),
        ("direct_mode", "Direct connection mode", "sdk-connection-mode"),
        ("gateway_mode", "Gateway connection mode", "sdk-connection-mode"),
        ("partition_key", "Partition key configured", "partition-high-cardinality"),
        ("bulk_operations", "Bulk operations", "sdk-bulk-operations"),
        ("etag_concurrency", "ETag optimistic concurrency", "sdk-etag-concurrency"),
        ("point_reads", "Point reads (by ID + partition key)", "query-avoid-scans"),
        ("cross_partition", "Cross-partition queries", "query-avoid-cross-partition"),
        ("indexing_policy", "Custom indexing policy", "index-exclude-unused"),
        ("throughput", "Throughput configuration", "throughput-provision-rus"),
        ("change_feed", "Change feed usage", "pattern-change-feed"),
        ("diagnostics", "Diagnostics/logging", "sdk-diagnostics"),
    ]

    for key, label, rule in pattern_labels:
        status = "Detected" if patterns.get(key, False) else "Not detected"
        lines.append(f"| {label} | {status} | `{rule}` |")

    lines.extend([
        "",
        "## Test Results",
        "",
        f"**Pass rate: {pass_rate}%** ({result_text})",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Errors | {errors} |",
        f"| Skipped | {skipped} |",
        "",
    ])

    failures = report.get("failures", []) if report else []
    if failures:
        lines.append("### Failures")
        lines.append("")
        for f in failures:
            lines.append(f"- **{f.get('test', 'unknown')}**")
            lines.append(f"  > {f.get('message', '')[:200]}")
            lines.append("")

    if pass_rate == 100:
        lines.extend([
            "### All tests passed",
            "",
            "The generated application fully conforms to the API contract.",
            "",
        ])

    lines.extend([
        "## Source Files",
        "",
        f"Source code archived in `source-code.zip` ({len(source_files)} files).",
        "",
    ])

    lines.extend([
        "## Score Summary",
        "",
        "| Category | Score | Notes |",
        "|----------|-------|-------|",
        f"| API Conformance | {score}/10 | {pass_rate}% pass rate |",
        f"| **Overall** | **{score}/10** | **{result_text}** |",
        "",
    ])

    return "\n".join(lines)


def update_improvements_log(scenario, iteration, report):
    """Add or replace an entry in IMPROVEMENTS-LOG.md."""
    log_path = Path("testing-v2/IMPROVEMENTS-LOG.md")
    if not log_path.exists():
        print(f"  {log_path} not found, skipping")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = report.get("summary", {}) if report else {}
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    pass_rate = summary.get("pass_rate", 0)
    score = compute_score(report)

    language = iteration.rsplit("-", 1)[-1] if "-" in iteration else "unknown"
    scenario_title = scenario.replace("-", " ").title()

    if pass_rate == 100:
        result_line = f"SUCCESSFUL -- {total}/{total} tests passed (100%)"
    elif pass_rate >= 50:
        result_line = f"PARTIAL -- {passed}/{total} tests passed ({pass_rate}%)"
    else:
        result_line = f"FAILED -- {passed}/{total} tests passed ({pass_rate}%)"

    entry_lines = [
        f"#### {now}: {iteration} - {scenario_title} ({language.title()})",
        "",
        f"- **Scenario**: {scenario}",
        f"- **Iteration**: {iteration}",
        f"- **Result**: {result_line}",
        f"- **Score**: {score}/10",
        "",
    ]

    failures = report.get("failures", []) if report else []
    if failures:
        entry_lines.append("**Issues Encountered**:")
        for f in failures[:10]:
            msg = f.get("message", "")[:100]
            entry_lines.append(f"1. **{f.get('test', 'unknown')}** -- {msg}")
        entry_lines.append("")

    entry_lines.extend([
        f"**Test Results**: {passed} passed, {total - passed} failed out of {total}",
        "",
    ])

    new_entry = "\n".join(entry_lines)
    content = log_path.read_text(encoding="utf-8")

    # Check if entry for this iteration already exists and replace it
    pattern = rf"#### \d{{4}}-\d{{2}}-\d{{2}}: {re.escape(iteration)} - .*"
    match = re.search(pattern, content)

    if match:
        start = match.start()
        # Find the next entry header or end of file
        rest = content[match.end():]
        next_entry = re.search(r"\n####\s", rest)
        if next_entry:
            end = match.end() + next_entry.start()
        else:
            end = len(content)
        content = content[:start] + new_entry + content[end:]
        print(f"  Replaced existing entry in {log_path}")
    else:
        content = content.rstrip() + "\n\n" + new_entry
        print(f"  Appended new entry to {log_path}")

    log_path.write_text(content, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    scenario = os.environ.get("SCENARIO", "unknown")
    iteration = os.environ.get("ITERATION", "unknown")
    iteration_dir = os.environ.get("ITERATION_DIR", "")

    if not iteration_dir:
        print("ERROR: ITERATION_DIR not set")
        sys.exit(1)

    print(f"Evaluating {scenario} / {iteration}")
    print(f"  Iteration dir: {iteration_dir}")

    report = load_test_results()
    if report:
        pr = report.get("summary", {}).get("pass_rate", 0)
        print(f"  Test results: {pr}% pass rate")
    else:
        print("  No test results found (test-report.json missing)")

    patterns = scan_code_patterns(iteration_dir)
    detected = [k for k, v in patterns.items() if v]
    print(f"  Patterns detected: {', '.join(detected) or 'none'}")

    source_files = list_source_files(iteration_dir)
    print(f"  Source files: {len(source_files)}")

    iteration_md = generate_iteration_md(
        scenario, iteration, report, patterns, source_files
    )
    md_path = Path(iteration_dir) / "ITERATION.md"
    md_path.write_text(iteration_md, encoding="utf-8")
    print(f"  Created {md_path}")

    if report:
        update_improvements_log(scenario, iteration, report)

    print("Evaluation complete")


if __name__ == "__main__":
    main()
