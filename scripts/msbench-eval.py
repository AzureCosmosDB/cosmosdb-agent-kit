#!/usr/bin/env python3
"""Run an MSBench benchmark, merge pass@k results, and flag failing instances.

Usage:
    python scripts/msbench-eval.py --benchmark cosmos-sdk-skills --repeat 3 --threshold 0.9
    python scripts/msbench-eval.py --dry-run

The script submits a single ``msbench-cli run`` command, optionally waits for the
run to finish by polling ``msbench-cli resume``, generates a merged report with
``msbench-cli report --merge pass_at_k``, parses per-instance pass rates from the
report JSON, and invokes ``scripts/create-skills-issue.py`` when any scenario × SDK
instance falls below the configured threshold.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_BENCHMARK = "cosmos-sdk-skills"
DEFAULT_REPEAT = 3
DEFAULT_THRESHOLD = 0.9
DEFAULT_OUTPUT = "results.json"
POLL_INTERVAL_SECONDS = 30
MAX_POLLS = 120
RUN_ID_PATTERNS = (
    r'"run_id"\s*:\s*"([^"]+)"',
    r"\brun[_ -]?id\b\s*[:=]\s*([A-Za-z0-9._:-]+)",
    r"\bRun ID\b\s*[:=]\s*([A-Za-z0-9._:-]+)",
)
STATUS_PATTERNS = (
    r'"status"\s*:\s*"([^"]+)"',
    r"\bstatus\b\s*[:=]\s*([A-Za-z0-9._-]+)",
)
TERMINAL_SUCCESS = {"completed", "complete", "succeeded", "success", "finished", "done"}
TERMINAL_FAILURE = {"failed", "error", "cancelled", "canceled", "aborted"}
NON_TERMINAL = {"queued", "pending", "running", "resuming", "in_progress", "in-progress", "submitted"}
PASS_RATE_KEYS = (
    "pass_at_k",
    "pass@k",
    "pass_rate",
    "passrate",
    "pass",
    "score",
)
INSTANCE_ID_KEYS = ("instance_id", "instance", "instance_name", "id", "name", "task_id")
SCENARIO_KEYS = ("scenario", "scenario_name")
SDK_KEYS = ("sdk", "sdk_name", "language", "lang")
SKIP_CONTAINER_KEYS = {"summary", "overall", "aggregated", "aggregate", "totals", "metadata"}


class MsbenchEvalError(RuntimeError):
    """Raised when the benchmark workflow cannot complete."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an MSBench benchmark and evaluate per-instance pass thresholds."
    )
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK, help="Benchmark name")
    parser.add_argument("--repeat", type=int, default=DEFAULT_REPEAT, help="Repeat count")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Minimum acceptable pass rate from 0.0 to 1.0",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Report output JSON path")
    parser.add_argument("--agent", help="Optional msbench agent value")
    parser.add_argument("--model", help="Optional msbench model value")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Submit the run and exit without polling/report generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
    args = parser.parse_args()

    if args.repeat <= 0:
        parser.error("--repeat must be greater than zero")
    if not 0 <= args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")

    return args


def quote_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def ensure_msbench_installed(dry_run: bool) -> None:
    if dry_run:
        return
    if shutil.which("msbench-cli") is None:
        raise MsbenchEvalError(
            "msbench-cli was not found on PATH. Install it first (for example: pip install msbench-cli)."
        )


def run_command(
    command: list[str],
    *,
    dry_run: bool = False,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str] | None:
    rendered = quote_command(command)
    print(f"> {rendered}")
    if dry_run:
        return None

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise MsbenchEvalError(f"Command not found: {command[0]}") from exc
    except OSError as exc:
        raise MsbenchEvalError(f"Failed to start command: {rendered}\n{exc}") from exc

    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)

    if check and completed.returncode != 0:
        error_hint = ""
        combined = f"{completed.stdout}\n{completed.stderr}".lower()
        if "login" in combined or "unauthorized" in combined or "forbidden" in combined or "auth" in combined:
            error_hint = "\nAuthentication may be required. Verify your msbench/Azure credentials."
        raise MsbenchEvalError(
            f"Command failed with exit code {completed.returncode}: {rendered}{error_hint}"
        )

    return completed


def extract_run_id(text: str) -> str | None:
    for pattern in RUN_ID_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"')
    return None


def extract_status(text: str) -> str | None:
    for pattern in STATUS_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"').lower()
    lowered = text.lower()
    for status in TERMINAL_SUCCESS | TERMINAL_FAILURE | NON_TERMINAL:
        if re.search(rf"\b{re.escape(status)}\b", lowered):
            return status
    return None


def build_run_command(args: argparse.Namespace) -> list[str]:
    command = [
        "msbench-cli",
        "run",
        "--benchmark",
        args.benchmark,
        "--repeat",
        str(args.repeat),
    ]
    if args.agent:
        command.extend(["--agent", args.agent])
    if args.model:
        command.extend(["--model", args.model])
    return command


def build_resume_command(run_id: str, args: argparse.Namespace) -> list[str]:
    command = ["msbench-cli", "resume", "--run_id", run_id]
    if args.agent:
        command.extend(["--agent", args.agent])
    if args.model:
        command.extend(["--model", args.model])
    return command


def build_report_command(run_id: str, output_path: Path) -> list[str]:
    return [
        "msbench-cli",
        "report",
        "--run_id",
        run_id,
        "--merge",
        "pass_at_k",
        "--output",
        str(output_path),
    ]


def resolve_output_path(raw_output: str) -> Path:
    output_path = Path(raw_output)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def wait_for_completion(run_id: str, args: argparse.Namespace) -> None:
    print(f"Polling run {run_id} until completion...")
    for attempt in range(1, MAX_POLLS + 1):
        completed = run_command(build_resume_command(run_id, args), dry_run=False, check=True)
        text = f"{completed.stdout}\n{completed.stderr}" if completed else ""
        status = extract_status(text)

        if status in TERMINAL_SUCCESS:
            print(f"Run {run_id} completed with status: {status}")
            return
        if status in TERMINAL_FAILURE:
            raise MsbenchEvalError(f"Run {run_id} finished with failure status: {status}")

        print(
            f"Run {run_id} status after poll {attempt}/{MAX_POLLS}: {status or 'unknown'}; "
            f"sleeping {POLL_INTERVAL_SECONDS}s"
        )
        time.sleep(POLL_INTERVAL_SECONDS)

    raise MsbenchEvalError(
        f"Run {run_id} did not reach a terminal state after {MAX_POLLS} polls."
    )


def normalize_rate(value: Any) -> float | None:
    """Normalize a pass rate to a 0.0–1.0 float.

    Handles: bool, numeric (0-1 as fraction, >1 as percentage), and strings
    with optional '%' suffix. A '%' suffix always means the number is a percentage.
    """
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        rate = float(value)
        if rate > 1.0 and rate <= 100.0:
            return rate / 100.0
        if 0.0 <= rate <= 1.0:
            return rate
        return None
    if isinstance(value, str):
        is_percent = value.strip().endswith("%")
        stripped = value.strip().rstrip("%")
        try:
            parsed = float(stripped)
        except ValueError:
            return None
        if is_percent:
            return parsed / 100.0
        return normalize_rate(parsed)
    return None


def first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def extract_instance_results(payload: Any) -> list[dict[str, Any]]:
    extracted: dict[str, dict[str, Any]] = {}

    def visit(node: Any, context: dict[str, Any]) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item, context)
            return

        if not isinstance(node, dict):
            return

        next_context = dict(context)
        scenario = first_present(node, SCENARIO_KEYS) or context.get("scenario")
        sdk = first_present(node, SDK_KEYS) or context.get("sdk")
        instance_id = first_present(node, INSTANCE_ID_KEYS) or context.get("instance_id")
        rate = first_present(node, PASS_RATE_KEYS)
        normalized_rate = normalize_rate(rate)

        if scenario:
            next_context["scenario"] = str(scenario)
        if sdk:
            next_context["sdk"] = str(sdk)
        if instance_id:
            next_context["instance_id"] = str(instance_id)

        explicit_instance_id = first_present(node, INSTANCE_ID_KEYS)
        explicit_scenario = first_present(node, SCENARIO_KEYS)
        explicit_sdk = first_present(node, SDK_KEYS)
        if normalized_rate is not None and (explicit_instance_id or (explicit_scenario and explicit_sdk)):
            label = (
                f"{next_context['scenario']} × {next_context['sdk']}"
                if next_context.get("scenario") and next_context.get("sdk")
                else str(explicit_instance_id or next_context.get("instance_id"))
            )
            extracted[label] = {
                "label": label,
                "scenario": next_context.get("scenario"),
                "sdk": next_context.get("sdk"),
                "instance_id": next_context.get("instance_id"),
                "pass_rate": normalized_rate,
            }

        for key, value in node.items():
            if key.lower() in SKIP_CONTAINER_KEYS:
                continue
            if isinstance(value, (dict, list)):
                visit(value, next_context)

    visit(payload, {})
    return sorted(extracted.values(), key=lambda item: item["label"])


def load_results(output_path: Path) -> list[dict[str, Any]]:
    if not output_path.exists():
        raise MsbenchEvalError(f"Report file not found: {output_path}")

    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MsbenchEvalError(f"Could not parse report JSON: {output_path}\n{exc}") from exc

    results = extract_instance_results(payload)
    if not results:
        raise MsbenchEvalError(
            "Could not find per-instance pass-rate records in the report JSON."
        )
    return results


def print_summary(results: list[dict[str, Any]], threshold: float) -> None:
    headers = ("Instance", "Pass Rate", "Threshold", "Status")
    rows = []
    for item in results:
        status = "PASS" if item["pass_rate"] >= threshold else "FAIL"
        rows.append(
            (
                item["label"],
                f"{item['pass_rate'] * 100:.1f}%",
                f"{threshold * 100:.1f}%",
                status,
            )
        )

    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(column)) for width, column in zip(widths, row)]

    def format_row(row: tuple[str, str, str, str]) -> str:
        return " | ".join(column.ljust(width) for column, width in zip(row, widths))

    print("\nSummary")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))


def invoke_issue_creator(output_path: Path, dry_run: bool) -> None:
    issue_script = Path(__file__).resolve().with_name("create-skills-issue.py")
    if not issue_script.exists():
        print(
            f"WARNING: Issue creator script not found at {issue_script}; skipping issue creation.",
            file=sys.stderr,
        )
        return

    command = [sys.executable, str(issue_script), "--results-file", str(output_path)]
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo:
        command.extend(["--repo", repo])

    try:
        run_command(command, dry_run=dry_run, check=True)
    except MsbenchEvalError as exc:
        print(f"WARNING: Issue creator failed: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    output_path = resolve_output_path(args.output)

    if args.dry_run:
        print("Dry run enabled; no commands will be executed.")
    else:
        ensure_msbench_installed(dry_run=False)

    initial = run_command(build_run_command(args), dry_run=args.dry_run, check=True)

    if args.no_wait:
        print("Run submitted with --no-wait; skipping polling, report generation, and threshold checks.")
        return 0

    if args.dry_run:
        print(
            "> msbench-cli resume --run_id <run_id>  # if the initial run is still in progress"
        )
        print(f"> {quote_command(build_report_command('<run_id>', output_path))}")
        print(
            "> python scripts/create-skills-issue.py --results-file "
            f"{output_path}  # only if threshold failures are found"
        )
        return 0

    combined_initial_output = f"{initial.stdout}\n{initial.stderr}"
    run_id = extract_run_id(combined_initial_output)
    if not run_id:
        raise MsbenchEvalError(
            "Unable to determine run_id from msbench-cli output."
        )

    initial_status = extract_status(combined_initial_output)
    if initial_status in TERMINAL_FAILURE:
        raise MsbenchEvalError(f"Run {run_id} failed immediately with status: {initial_status}")
    if initial_status not in TERMINAL_SUCCESS:
        wait_for_completion(run_id, args)

    run_command(build_report_command(run_id, output_path), dry_run=False, check=True)
    results = load_results(output_path)
    print_summary(results, args.threshold)

    failing = [item for item in results if item["pass_rate"] < args.threshold]
    if failing:
        print(
            f"\n{len(failing)} instance(s) fell below the {args.threshold * 100:.1f}% threshold.",
            file=sys.stderr,
        )
        return 1

    print("\nAll instances met the configured threshold.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MsbenchEvalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
