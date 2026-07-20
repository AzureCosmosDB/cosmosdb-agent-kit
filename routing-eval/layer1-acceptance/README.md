# Layer 1 - A/B acceptance (optional confirmation)

> Status: optional. The primary gate is the routing classifier in
> [`../src/route_classify.py`](../src/route_classify.py) (Layer 2). Layer 1 is a
> heavier end-to-end A/B you can run deliberately when making the monolith
> decision, but it largely reproduces the routing signal Layer 2 already gives you.
> A runnable staging helper ([`stage_skill_set.py`](stage_skill_set.py)) ships so
> the A/B is expressible; the scoring step reuses the existing **Vally** + Copilot
> SDK engine.

## Why this is optional, not the gate

The rules inside the split skills are the same rules that were in the monolith. So
when routing is correct, the agent applies identical content and produces the same
answer it would have under the monolith (modulo nondeterminism). That makes an
end-to-end answer A/B mostly a more expensive, noisier way to measure routing
correctness, which Layer 2 measures directly. Use Layer 2 as the gate. Reach for
Layer 1 only when you want an end-to-end sanity check before retiring the monolith,
or to probe the two things Layer 2 does not cover: multi-skill prompts and any
second-order effect of smaller, separately described skills.

## How the A/B works (and why the monolith is the baseline, not a problem)

The monolith has **no internal routing**: one skill, every rule present once
selected. That is exactly what makes it the clean baseline. Run the **same** prompts
end to end in two arms and compare final answer quality:

- **Baseline arm (monolith-only):** only `cosmosdb-best-practices` is available.
  One skill, no routing decision, all rules present. This is the no-routing ceiling.
- **Candidate arm (split-only):** only the 4 topic skills are available. The agent
  must choose which skill(s) to load before answering. A wrong choice loads the
  wrong rules and the answer degrades.

Because the rule content is identical and available in both arms, any drop in the
candidate arm is attributable to the **selection step**, not to missing rules. The
gap between the arms is the routing penalty.

## You do not delete the monolith

"Which skills are available" is controlled per run by pointing the runner at a
**staged, isolated skills directory**, not by mutating `skills/`. The helper
[`stage_skill_set.py`](stage_skill_set.py) builds these temp roots non-destructively:

```powershell
# Baseline arm: a temp root containing ONLY the monolith
python routing-eval/layer1-acceptance/stage_skill_set.py --arm monolith --out routing-eval/.tmp/skills-monolith

# Candidate arm: a temp root containing ONLY the 4 split skills
python routing-eval/layer1-acceptance/stage_skill_set.py --arm split --out routing-eval/.tmp/skills-split
```

Each command copies the relevant skill folders into the target directory. The real
`skills/` folder is never touched. Point the agent runtime at the staged root for
that arm as its skills source.

## Wiring the scoring step (if you run the full A/B)

The existing Vally eval targets a **named** skill
([`../../evals/cosmosdb-best-practices/eval.yaml`](../../evals/cosmosdb-best-practices/eval.yaml)),
so it force-loads one skill and does not route. A full Layer 1 is therefore a
two-stage pipeline per prompt:

1. **Routing stage.** Let something pick the skill from the staged set: either the
   Layer 2 classifier ([`../src/route_classify.py`](../src/route_classify.py)) as a
   fast deterministic stand-in, or a real agent runtime doing progressive disclosure
   when pointed at the staged skills root.
2. **Application stage.** Load the chosen skill's content and run the task through
   the `copilot-sdk` engine, scored with the same graders the content evals use
  ([`../../.vally.yaml`](../../.vally.yaml)), so both arms are scored identically.

Keep it local-first: Vally authenticates with the maintainer's own token, so no
upstream secret or org model-access grant is required to run it.
