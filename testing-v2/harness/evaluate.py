#!/usr/bin/env python3
"""
Automated evaluation of test iteration results.

Creates ITERATION.md in the iteration directory and updates
testing-v2/IMPROVEMENTS-LOG.md and CHANGELOG.md with the test results.

Environment variables (set by CI):
    SCENARIO       - scenario name (e.g., gaming-leaderboard)
    ITERATION      - iteration id (e.g., iteration-001-python)
    ITERATION_DIR  - path to iteration directory

Reads:
    test-report.json (current directory, created by report.py)

Writes:
    {ITERATION_DIR}/ITERATION.md
    testing-v2/IMPROVEMENTS-LOG.md (append or replace entry)
    CHANGELOG.md (prepend concise entry)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_test_results():
    """Load test-report.json and signal files from the current directory."""
    path = Path("test-report.json")
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))

    # Load build/startup signals if not already in the report
    if "build_signal" not in report:
        bs = Path("build-signal.json")
        if bs.exists():
            report["build_signal"] = json.loads(bs.read_text(encoding="utf-8"))

    if "startup_signal" not in report:
        ss = Path("startup-signal.json")
        if ss.exists():
            report["startup_signal"] = json.loads(ss.read_text(encoding="utf-8"))

    return report


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
    """
    Map pass rate to a 1-10 score, factoring in build/startup signals.

    Build failures and infrastructure test failures are weighted:
    - Build failure on first attempt: -1 from score
    - Startup failure: score capped at 1
    - Cosmos infrastructure test failures: -1 per 3 failures
    """
    if report is None or report.get("startup_failed"):
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

    # Penalize for build failure (first attempt) if signal is available
    build_signal = report.get("build_signal")
    if build_signal and not build_signal.get("succeeded", True):
        base = max(1, base - 1)

    # Penalize for cosmos infrastructure test failures
    categories = report.get("categories", {})
    infra = categories.get("cosmos_infrastructure", {})
    infra_failures = infra.get("failed", 0) + infra.get("errors", 0)
    if infra_failures > 0:
        penalty = (infra_failures + 2) // 3  # -1 per 3 failures
        base = max(1, base - penalty)

    return base


def generate_iteration_md(scenario, iteration, report, patterns, source_files, skills_loaded):
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

    run_type = "Normal run (skills loaded)" if skills_loaded else "Control run (NO skills loaded)"

    lines = [
        f"# {iteration} - {language.title()} {scenario_title}",
        "",
        "## Metadata",
        f"- **Date**: {now}",
        f"- **Language/SDK**: {language.title()}",
        f"- **Agent**: GitHub Copilot (automated iteration)",
        f"- **Tester**: Automated CI",
        f"- **Run Type**: {run_type}",
        "",
        "## Skills Verification",
        "",
    ]

    if skills_loaded:
        lines.append("**Were skills loaded before building?** Yes (via issue prompt referencing AGENTS.md)")
    else:
        lines.extend([
            "**Were skills loaded before building?** No (CONTROL RUN)",
            "",
            "> This is a control run. The agent generated code using only its built-in",
            "> knowledge, without reading the Cosmos DB best practices skills.",
            "> The evaluation below identifies which existing rules would have helped.",
        ])

    lines.extend([
        "",
        "## Cosmos DB Patterns Detected",
        "",
        "| Pattern | Status | Related Rule |",
        "|---------|--------|--------------|",
    ])

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

    # Build & Startup Signals section
    build_signal = report.get("build_signal") if report else None
    startup_signal = report.get("startup_signal") if report else None
    if build_signal or startup_signal:
        lines.extend(["## Build & Startup Signals", ""])
        if build_signal:
            build_ok = build_signal.get("succeeded", True)
            lines.append(f"- **Build**: {'PASS' if build_ok else 'FAIL'}")
            if not build_ok:
                stderr = build_signal.get("stderr_tail", "")
                if stderr:
                    lines.extend(["  ```", f"  {stderr[:500]}", "  ```"])
        if startup_signal:
            start_ok = startup_signal.get("startup_succeeded", True)
            lines.append(f"- **Startup**: {'PASS' if start_ok else 'FAIL'}")
            if not start_ok:
                err = startup_signal.get("error", "")
                if err:
                    lines.append(f"  > {err[:300]}")
        lines.append("")

    # Results by Category section
    categories = report.get("categories", {}) if report else {}
    if categories:
        lines.extend([
            "## Results by Category",
            "",
            "| Category | Passed | Failed | Skipped |",
            "|----------|--------|--------|---------|",
        ])
        for cat, counts in sorted(categories.items()):
            lines.append(
                f"| {cat} | {counts.get('passed', 0)} | "
                f"{counts.get('failed', 0) + counts.get('errors', 0)} | "
                f"{counts.get('skipped', 0)} |"
            )
        lines.append("")

    # Score Summary
    score_notes = [f"{pass_rate}% pass rate"]
    if build_signal and not build_signal.get("succeeded", True):
        score_notes.append("build failure penalty")
    infra = categories.get("cosmos_infrastructure", {})
    infra_failures = infra.get("failed", 0) + infra.get("errors", 0)
    if infra_failures > 0:
        score_notes.append(f"{infra_failures} infrastructure failures")

    lines.extend([
        "## Score Summary",
        "",
        "| Category | Score | Notes |",
        "|----------|-------|-------|",
        f"| API Conformance | {score}/10 | {'; '.join(score_notes)} |",
        f"| **Overall** | **{score}/10** | **{result_text}** |",
        "",
    ])

    return "\n".join(lines)


def update_improvements_log(scenario, iteration, report, skills_loaded):
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
    run_type = "skills loaded" if skills_loaded else "CONTROL - no skills"

    if pass_rate == 100:
        result_line = f"SUCCESSFUL -- {total}/{total} tests passed (100%)"
    elif pass_rate >= 50:
        result_line = f"PARTIAL -- {passed}/{total} tests passed ({pass_rate}%)"
    else:
        result_line = f"FAILED -- {passed}/{total} tests passed ({pass_rate}%)"

    entry_lines = [
        f"#### {now}: {iteration} - {scenario_title} ({language.title()}) [{run_type}]",
        "",
        f"- **Scenario**: {scenario}",
        f"- **Iteration**: {iteration}",
        f"- **Skills loaded**: {'Yes' if skills_loaded else 'No (control run)'}",
        f"- **Result**: {result_line}",
        f"- **Score**: {score}/10",
        "",
    ]

    # Add category breakdown if available
    categories = report.get("categories", {}) if report else {}
    if categories:
        entry_lines.append("**Results by Category**:")
        for cat, counts in sorted(categories.items()):
            cat_failed = counts.get("failed", 0) + counts.get("errors", 0)
            entry_lines.append(
                f"- {cat}: {counts.get('passed', 0)} passed, "
                f"{cat_failed} failed, {counts.get('skipped', 0)} skipped"
            )
        entry_lines.append("")

    # Add build signal if available
    build_signal = report.get("build_signal") if report else None
    if build_signal and not build_signal.get("succeeded", True):
        entry_lines.append("**Build failure on first attempt**")
        entry_lines.append("")

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


def update_changelog(scenario, iteration, report, skills_loaded):
    """Prepend a concise entry to CHANGELOG.md."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print(f"  {changelog_path} not found, skipping")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = report.get("summary", {}) if report else {}
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    pass_rate = summary.get("pass_rate", 0)
    score = compute_score(report)

    language = iteration.rsplit("-", 1)[-1] if "-" in iteration else "unknown"
    run_type = "skills" if skills_loaded else "control"

    entry_lines = [
        f"## {now} \u2014 {iteration} automated evaluation ({run_type})",
        "",
        f"- **Scenario**: {scenario}, **Language**: {language}",
        f"- **Result**: {passed}/{total} tests passed ({pass_rate}%), score {score}/10",
    ]
    if not skills_loaded:
        entry_lines.append("- Control run (no skills loaded)")
    entry_lines.append("")

    new_entry = "\n".join(entry_lines)
    content = changelog_path.read_text(encoding="utf-8")

    # Insert after the first --- separator line
    separator = "\n---\n"
    sep_pos = content.find(separator)
    if sep_pos != -1:
        insert_pos = sep_pos + len(separator)
        content = content[:insert_pos] + "\n" + new_entry + content[insert_pos:]
    else:
        # Fallback: append after first heading
        content = content.rstrip() + "\n\n" + new_entry

    changelog_path.write_text(content, encoding="utf-8")
    print(f"  Added entry to {changelog_path}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    scenario = os.environ.get("SCENARIO", "unknown")
    iteration = os.environ.get("ITERATION", "unknown")
    iteration_dir = os.environ.get("ITERATION_DIR", "")
    skills_loaded = os.environ.get("SKILLS_LOADED", "True") == "True"

    if not iteration_dir:
        print("ERROR: ITERATION_DIR not set")
        sys.exit(1)

    print(f"Evaluating {scenario} / {iteration}")
    print(f"  Iteration dir: {iteration_dir}")
    print(f"  Skills loaded: {skills_loaded}")

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
        scenario, iteration, report, patterns, source_files, skills_loaded
    )
    md_path = Path(iteration_dir) / "ITERATION.md"
    md_path.write_text(iteration_md, encoding="utf-8")
    print(f"  Created {md_path}")

    if report:
        update_improvements_log(scenario, iteration, report, skills_loaded)
        update_changelog(scenario, iteration, report, skills_loaded)

    print("Evaluation complete")


if __name__ == "__main__":
    main()
