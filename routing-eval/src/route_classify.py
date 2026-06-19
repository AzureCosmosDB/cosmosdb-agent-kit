"""Layer 2 - routing classifier (the diagnostic).

Isolates the skill-SELECTION step. For each labeled prompt it presents the model
with ONLY the skill names and descriptions (mirroring the startup state a real
agent sees) and asks which single skill it would load to answer the question. It
does NOT let the model answer the question itself - we only capture the routing
decision and compare it to the expected skill.

Output: per-skill accuracy, an overall score, a confusion matrix, and a list of
every misroute (which skill stole the prompt). That tells you exactly which
descriptions to sharpen, rather than just a lower aggregate number.

Two arms:
  --arm split   the 13 topic skills only (no monolith)   [default]
  --arm all     topic skills plus the monolith catch-all

In the "all" arm, a prompt routed to the monolith counts as a miss against a
specific-skill expectation. That is intentional: selecting the monolith defeats
the point of the split, so we want to see how often it absorbs traffic.

This is a local maintainer tool. It reads no upstream secrets and is not wired
to run in CI. See routing-eval/README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a plain script: python routing-eval/src/route_classify.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

PROMPTS_PATH = common.REPO_ROOT / "routing-eval" / "prompts" / "labeled-prompts.yaml"
RESULTS_DIR = common.REPO_ROOT / "routing-eval" / "results"

SYSTEM_PROMPT = """You are the skill router for an AI coding agent.
You are given a catalog of available skills, each with a name and a description.
Given a user's question, decide which SINGLE skill should be loaded to answer it.
Choose the skill whose description best matches the question. If genuinely no
skill fits, return "none".

Respond with ONLY a compact JSON object and nothing else:
{"skill": "<skill-name-or-none>"}"""


def build_catalog(skills: list[common.Skill]) -> str:
    blocks = []
    for s in skills:
        blocks.append(f"- name: {s.name}\n  description: |\n    " + s.description.replace("\n", "\n    "))
    return "\n".join(blocks)


def classify_one(client, model: str, catalog: str, prompt: str) -> str:
    user_msg = f"SKILL CATALOG:\n{catalog}\n\nUSER QUESTION:\n{prompt}"
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    return _extract_skill(content)


def _extract_skill(content: str) -> str:
    # Tolerate code fences or stray prose around the JSON object.
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            obj = json.loads(content[start : end + 1])
            return str(obj.get("skill", "")).strip() or "unparsed"
        except json.JSONDecodeError:
            pass
    return "unparsed"


def run(arm: str, model: str, limit: int | None) -> dict:
    include_monolith = arm == "all"
    skills = common.load_skills(include_monolith=include_monolith)
    valid_names = {s.name for s in skills} | {"none"}
    catalog = build_catalog(skills)
    prompts = common.load_prompts(PROMPTS_PATH)
    if limit:
        prompts = prompts[:limit]

    client = common.get_model_client()

    per_skill = defaultdict(lambda: {"total": 0, "correct": 0})
    confusion = defaultdict(lambda: defaultdict(int))  # expected -> selected -> count
    misroutes = []
    rows = []

    for p in prompts:
        selected = classify_one(client, model, catalog, p.prompt)
        if selected not in valid_names:
            selected = f"invalid:{selected}"
        acceptable = {p.expected_skill, *p.also_acceptable}
        correct = selected in acceptable
        per_skill[p.expected_skill]["total"] += 1
        per_skill[p.expected_skill]["correct"] += int(correct)
        confusion[p.expected_skill][selected] += 1
        rows.append({"id": p.id, "expected": p.expected_skill, "selected": selected, "correct": correct})
        if not correct:
            misroutes.append({"id": p.id, "expected": p.expected_skill, "selected": selected, "prompt": p.prompt})
        marker = "OK " if correct else "XX "
        print(f"{marker}{p.id:<16} expected={p.expected_skill:<28} selected={selected}")

    total = len(rows)
    correct_total = sum(r["correct"] for r in rows)
    overall = correct_total / total if total else 0.0

    summary = {
        "arm": arm,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_accuracy": round(overall, 4),
        "total_prompts": total,
        "correct": correct_total,
        "per_skill": {
            name: {
                "total": v["total"],
                "correct": v["correct"],
                "accuracy": round(v["correct"] / v["total"], 4) if v["total"] else None,
            }
            for name, v in sorted(per_skill.items())
        },
        "confusion_matrix": {exp: dict(sel) for exp, sel in confusion.items()},
        "misroutes": misroutes,
        "rows": rows,
    }
    return summary


def print_report(summary: dict) -> None:
    print("\n" + "=" * 60)
    print(f"ROUTING EVAL  arm={summary['arm']}  model={summary['model']}")
    print("=" * 60)
    print(f"Overall accuracy: {summary['overall_accuracy']:.1%} "
          f"({summary['correct']}/{summary['total_prompts']})")
    print("\nPer-skill accuracy:")
    for name, v in summary["per_skill"].items():
        acc = "n/a" if v["accuracy"] is None else f"{v['accuracy']:.0%}"
        print(f"  {name:<30} {v['correct']}/{v['total']:<3} {acc}")
    if summary["misroutes"]:
        print("\nMisroutes (expected -> selected):")
        for m in summary["misroutes"]:
            print(f"  {m['id']:<16} {m['expected']} -> {m['selected']}")
    else:
        print("\nNo misroutes.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Routing classifier (Layer 2 diagnostic).")
    parser.add_argument("--arm", choices=["split", "all"], default="split",
                        help="split = 13 topic skills only; all = topic skills + monolith")
    parser.add_argument("--model", default=common.default_model(), help="model id (provider-specific)")
    parser.add_argument("--limit", type=int, default=None, help="only run the first N prompts")
    parser.add_argument("--out", default=None, help="path to write the JSON report")
    args = parser.parse_args()

    summary = run(arm=args.arm, model=args.model, limit=args.limit)
    print_report(summary)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"routing-{args.arm}-{stamp}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nReport written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
