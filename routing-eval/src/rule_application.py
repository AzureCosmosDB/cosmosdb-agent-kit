"""Angle 2 - Rule-application A/B (transitional).

Question this answers
---------------------
With the monolith, the right rule is sometimes present but buried in a large,
overloaded context and never gets applied. Does the focused split surface it more
reliably? This does NOT grade answer quality (too noisy). It checks one binary
thing per prompt: did the answer actually apply the governing rule, yes or no.

How it runs
-----------
For each prompt we run two arms and compare the rule-application rate:

  monolith arm : inject the FULL monolith AGENTS.md (every rule, ~125k tokens) as
                 guidance, then answer. No routing; the model must find the rule in
                 the overloaded context.
  split arm    : inject ONLY the expected skill's AGENTS.md (the focused subset),
                 then answer. The relevant rule is far more salient.

A separate judge call decides, per arm, whether the governing rule was applied.
The split arm injects the correct skill on purpose: this isolates the context-size
(dilution) effect from skill routing. Routing itself is measured by Angle 1
(route_classify.py).

Why this is transitional
------------------------
It is inherently a monolith-vs-split comparison. Once the monolith is archived
there is no baseline arm left, so this harness goes dormant. Run it now to inform
the retire/archive decision, then keep it and its results archived for posterity.

Local + repeatable
------------------
Reuses the same OpenAI-compatible client as Angle 1 (your own GITHUB_TOKEN, no repo
secrets). The monolith arm is near a 128k context window; if a model rejects it for
length, that prompt's monolith arm is recorded as `context_overflow`, which is
itself evidence for the split.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from common import (
    MONOLITH_NAME,
    REPO_ROOT,
    SKILLS_DIR,
    default_model,
    get_model_client,
)

PROMPTS_PATH = REPO_ROOT / "routing-eval" / "prompts" / "rule-application-prompts.yaml"
RESULTS_DIR = REPO_ROOT / "routing-eval" / "results"


@dataclass(frozen=True)
class RulePrompt:
    id: str
    expected_skill: str
    expected_rules: tuple[str, ...]
    prompt: str


def load_rule_prompts(path: Path) -> list[RulePrompt]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("prompts", [])
    prompts = []
    for item in raw:
        # Accept either a single `expected_rule` or a list `expected_rules`.
        if "expected_rules" in item:
            rules = tuple(str(r) for r in item["expected_rules"])
        else:
            rules = (str(item["expected_rule"]),)
        if not rules:
            raise ValueError(f"Prompt {item.get('id')} has no expected rule(s)")
        prompts.append(
            RulePrompt(
                id=str(item["id"]),
                expected_skill=str(item["expected_skill"]),
                expected_rules=rules,
                prompt=str(item["prompt"]),
            )
        )
    if not prompts:
        raise RuntimeError(f"No prompts found in {path}")
    return prompts


def skill_content(directory: str) -> str:
    path = SKILLS_DIR / directory / "AGENTS.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing compiled rules: {path}")
    return path.read_text(encoding="utf-8")


def rule_text(rule_basename: str) -> str:
    path = SKILLS_DIR / MONOLITH_NAME / "rules" / f"{rule_basename}.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing rule file: {path}")
    return path.read_text(encoding="utf-8")


def pick_wrong_skill(expected_skill: str) -> str:
    """Pick a deterministically unrelated skill for the wrong-context no-rule arm.

    The chosen skill must NOT contain the prompt's governing rule, so that any
    "applied" verdict in this arm comes from the model's own prior knowledge
    rather than the supplied guidance. The four skills hold disjoint rule sets,
    so any skill other than the expected one is a valid wrong context.
    """
    return "cosmosdb-ai-and-search" if expected_skill == "cosmosdb-operations" else "cosmosdb-operations"


def approx_tokens(text: str) -> int:
    # Rough heuristic (~4 chars/token); only used for reporting, not billing.
    return len(text) // 4


ASSISTANT_SYSTEM = (
    "You are an expert Azure Cosmos DB engineer. Using ONLY the best-practice "
    "guidance provided below, give concrete, specific advice for the user's "
    "scenario. Apply whichever guidance is relevant; be direct and practical. Do "
    "not hedge with generic database advice that is not in the guidance.\n\n"
    "=== BEST PRACTICE GUIDANCE ===\n{context}"
)

JUDGE_SYSTEM = (
    "You are a strict evaluator. You are given a specific best-practice RULE, a "
    "user QUESTION, and an ASSISTANT ANSWER. Decide whether the answer actually "
    "applies the practice described in the rule, meaning it recommends or "
    "implements that specific practice for this scenario. Adjacent or generic "
    "advice that does not embody the rule counts as NOT applied. Respond with "
    'strict JSON only: {"applied": true|false, "reason": "<one short sentence>"}.'
)


def generate_answer(client, model: str, context: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": ASSISTANT_SYSTEM.format(context=context)},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""


def judge_applied(client, model: str, rule: str, prompt: str, answer: str) -> tuple[bool, str]:
    user = (
        f"RULE:\n{rule}\n\nQUESTION:\n{prompt}\n\nASSISTANT ANSWER:\n{answer}"
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    applied, reason = _parse_judge(raw)
    return applied, reason


def _parse_judge(raw: str) -> tuple[bool, str]:
    text = raw.strip()
    if text.startswith("```"):
        # strip code fences if the model wrapped the JSON
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        obj = json.loads(text)
        return bool(obj.get("applied", False)), str(obj.get("reason", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        # Tolerant fallback: look for an explicit boolean token.
        low = raw.lower()
        if '"applied": true' in low or "applied: true" in low:
            return True, "parsed-from-text"
        return False, "unparseable-judge-response"


def _is_context_overflow(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "context length",
            "context_length",
            "maximum context",
            "too many tokens",
            "string too long",
            "tokens_limit_reached",
            "request body too large",
            "max size",
            "413",
        )
    )


def run(model: str, limit: int | None) -> dict:
    client = get_model_client()
    prompts = load_rule_prompts(PROMPTS_PATH)
    if limit:
        prompts = prompts[:limit]

    monolith_ctx = skill_content(MONOLITH_NAME)
    monolith_tokens = approx_tokens(monolith_ctx)

    rows = []
    monolith_hits = 0
    split_hits = 0
    no_rule_hits = 0
    monolith_scored = 0
    split_scored = 0
    no_rule_scored = 0
    overflow = 0

    def score_arm(context: str, rules: dict[str, str]) -> tuple[bool, str, dict[str, bool]]:
        answer = generate_answer(client, model, context, p.prompt)
        per_rule: dict[str, bool] = {}
        for name, text in rules.items():
            applied, _ = judge_applied(client, model, text, p.prompt, answer)
            per_rule[name] = applied
        hit = all(per_rule.values())
        reason = "all rules applied" if hit else "missing: " + ", ".join(
            n for n, ok in per_rule.items() if not ok
        )
        return hit, reason, per_rule

    for p in prompts:
        split_ctx = skill_content(p.expected_skill)
        wrong_skill = pick_wrong_skill(p.expected_skill)
        wrong_ctx = skill_content(wrong_skill)
        rules = {name: rule_text(name) for name in p.expected_rules}

        # Monolith arm (overloaded context, no routing).
        m_applied: bool | None
        m_reason: str
        m_per_rule: dict[str, bool] = {}
        try:
            m_applied, m_reason, m_per_rule = score_arm(monolith_ctx, rules)
            monolith_scored += 1
            if m_applied:
                monolith_hits += 1
        except Exception as exc:  # noqa: BLE001 - record, do not crash the run
            if _is_context_overflow(exc):
                m_applied, m_reason = None, "context_overflow"
                overflow += 1
            else:
                m_applied, m_reason = None, f"error: {exc}"

        # Split arm (focused context: the correct skill).
        s_applied: bool | None
        s_reason: str
        s_per_rule: dict[str, bool] = {}
        try:
            s_applied, s_reason, s_per_rule = score_arm(split_ctx, rules)
            split_scored += 1
            if s_applied:
                split_hits += 1
        except Exception as exc:  # noqa: BLE001
            s_applied, s_reason = None, f"error: {exc}"

        # No-rule arm (wrong context: an unrelated skill lacking the governing
        # rule). This SHOULD score low; if it scores as high as the split arm,
        # the model's prior knowledge - not the supplied guidance - is driving
        # rule application, which would weaken the A/B's attribution.
        nr_applied: bool | None
        nr_reason: str
        nr_per_rule: dict[str, bool] = {}
        try:
            nr_applied, nr_reason, nr_per_rule = score_arm(wrong_ctx, rules)
            no_rule_scored += 1
            if nr_applied:
                no_rule_hits += 1
        except Exception as exc:  # noqa: BLE001
            nr_applied, nr_reason = None, f"error: {exc}"

        rows.append(
            {
                "id": p.id,
                "expected_skill": p.expected_skill,
                "expected_rules": list(p.expected_rules),
                "monolith_applied": m_applied,
                "monolith_reason": m_reason,
                "monolith_per_rule": m_per_rule,
                "split_applied": s_applied,
                "split_reason": s_reason,
                "split_per_rule": s_per_rule,
                "no_rule_skill": wrong_skill,
                "no_rule_applied": nr_applied,
                "no_rule_reason": nr_reason,
                "no_rule_per_rule": nr_per_rule,
                "split_tokens": approx_tokens(split_ctx),
            }
        )

        mark = {True: "OK", False: "XX", None: "--"}
        print(
            f"  [{p.id}] monolith={mark[m_applied]}  split={mark[s_applied]}  "
            f"no-rule={mark[nr_applied]}  ({', '.join(p.expected_rules)})"
        )

    return {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "monolith_tokens_approx": monolith_tokens,
        "counts": {
            "prompts": len(prompts),
            "monolith_scored": monolith_scored,
            "monolith_hits": monolith_hits,
            "split_scored": split_scored,
            "split_hits": split_hits,
            "no_rule_scored": no_rule_scored,
            "no_rule_hits": no_rule_hits,
            "monolith_context_overflow": overflow,
        },
        "rows": rows,
    }


def _rate(hits: int, scored: int) -> str:
    if scored == 0:
        return "n/a"
    return f"{hits / scored * 100:.1f}% ({hits}/{scored})"


def print_report(report: dict) -> None:
    c = report["counts"]
    print("\n" + "=" * 60)
    print(f"RULE-APPLICATION A/B (Angle 2)  model={report['model']}")
    print("=" * 60)
    print(f"Monolith context: ~{report['monolith_tokens_approx']} tokens")
    if c["monolith_context_overflow"]:
        print(f"Monolith context_overflow on {c['monolith_context_overflow']} prompt(s)")
    print(f"Monolith rule-application rate: {_rate(c['monolith_hits'], c['monolith_scored'])}")
    print(f"Split    rule-application rate: {_rate(c['split_hits'], c['split_scored'])}")
    print(f"No-rule  rule-application rate: {_rate(c['no_rule_hits'], c['no_rule_scored'])}  (wrong context; want LOW)")
    print("\nMisses (rule NOT applied):")
    any_miss = False
    for row in report["rows"]:
        flags = []
        if row["monolith_applied"] is False:
            flags.append("monolith")
        if row["monolith_applied"] is None:
            flags.append(f"monolith({row['monolith_reason']})")
        if row["split_applied"] is False:
            flags.append("split")
        if row["split_applied"] is None:
            flags.append(f"split({row['split_reason']})")
        if flags:
            any_miss = True
            rules_label = ", ".join(row["expected_rules"])
            print(f"  {row['id']:<18} {rules_label:<40} {', '.join(flags)}")
    if not any_miss:
        print("  none")


def write_results(report: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Angle 2 - rule-application A/B (monolith vs split).")
    parser.add_argument("--model", default=default_model(), help="Model id (default from ROUTING_EVAL_MODEL).")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N prompts.")
    parser.add_argument("--out", default=None, help="Path for the JSON report (default results/rule-application-<ts>.json).")
    args = parser.parse_args(argv)

    print(f"Running rule-application A/B  model={args.model}")
    report = run(model=args.model, limit=args.limit)
    print_report(report)

    if args.out:
        out_path = Path(args.out)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"rule-application-{ts}.json"
    write_results(report, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
