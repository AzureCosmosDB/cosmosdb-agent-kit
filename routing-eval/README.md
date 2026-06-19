# Routing Eval

A **local, on-demand** harness for testing whether an AI coding agent routes a
question to the **correct skill** now that `cosmosdb-best-practices` has been
split into 13 topic-specific skills.

It is **not** wired into CI and reads **no** repository secrets. You run it on
your own machine with your own model credentials.

---

## Why this exists

When there was a single monolith skill, an agent never had to choose: it loaded
the one skill and got every rule. After the split there are 13 topic skills, and
the agent must first decide **which** skill to load, based only on each skill's
`name` and `description` (the part loaded at startup). That selection step is a
**new risk** the split introduces.

Our existing test approaches (waza content evals, MSBench, scope) inject a chosen
skill's rules straight into context. They validate **rule content** but bypass the
**routing** decision entirely. This harness fills that gap.

Neither angle below grades output quality. Output scoring is dominated by
generation noise, so differences wash out. Both angles validate whether the **right
thing was chosen**, at two different granularities.

| Angle | What it validates | Lifespan | Cost / noise | Where |
|-------|-------------------|----------|--------------|-------|
| **1. Skill routing** (runnable) | Given only names + descriptions, did the agent pick the right **skill**? | **Permanent.** Re-run whenever a skill is added or a description changes. | Cheap, deterministic | [`src/route_classify.py`](src/route_classify.py) |
| **2. Rule-application A/B** (runnable, transitional) | Did the right **rule** actually get applied, and does the monolith's overloaded context cause misses the split fixes? | **Transitional.** Run now to justify retiring the monolith; archive with the monolith for posterity. | Heavier, low noise (binary rule hit) | [`src/rule_application.py`](src/rule_application.py) (a heavier full-agent variant is documented in [`layer1-acceptance/`](layer1-acceptance/README.md)) |

**Angle 1 is the keeper.** It directly measures the one new risk the split
introduces (picking the wrong skill), cheaply and without agent nondeterminism, and
pinpoints which descriptions overlap via a per-skill accuracy breakdown and a
confusion matrix. It auto-discovers whatever skills exist, so it stays valid as the
set grows. Run it before merging any change to a skill `name` or `description`.

**Angle 2 is transitional, by design.** It exists to answer one question: with the
monolith, the right rule is sometimes present but buried in an overloaded context
and never applied; does the focused split surface it more reliably? It is inherently
a monolith-vs-split comparison, so once the monolith is archived there is no baseline
left and it goes dormant. Run it now to make the retirement call, then keep it
archived alongside the monolith for posterity, not as a recurring gate. It measures
a **rule-application rate** (binary "was the governing rule applied", aggregated),
never a quality score.

---

## How routing is tested (Angle 1)

For each labeled prompt, the classifier shows the model **only** the skill names
and descriptions (mirroring the agent's startup state) and asks which single skill
it would load. It does **not** let the model answer the question. It captures the
choice and compares it to the expected skill.

Two arms:

- `--arm split` (default): the 13 topic skills only.
- `--arm all`: the 13 topic skills **plus** the monolith catch-all. A prompt that
  routes to the monolith counts as a miss against a specific-skill expectation,
  which is how we measure how much traffic the monolith absorbs.

The labeled corpus lives in [`prompts/labeled-prompts.yaml`](prompts/labeled-prompts.yaml).
Prompts are phrased the way a real developer would ask, avoiding the skill name, so
routing depends on the description rather than keyword echo.

---

## How rule application is tested (Angle 2)

For each prompt in [`prompts/rule-application-prompts.yaml`](prompts/rule-application-prompts.yaml)
(each with one or more governing rules) the harness runs three arms and asks a
judge, per arm, whether the answer actually **applied** the rule(s). A multi-rule
prompt counts as a hit only if every listed rule is applied:

- **Monolith arm:** inject the full monolith `AGENTS.md` (~125k tokens, every rule)
  as guidance, then answer. No routing; the model must find the rule in an
  overloaded context.
- **Split arm:** inject only the expected skill's `AGENTS.md` (the focused subset),
  then answer. The relevant rule is far more salient.
- **No-rule arm (wrong context):** inject an unrelated skill that does NOT contain
  the governing rule (`pick_wrong_skill`). This is a falsification check, not part
  of the A/B: it should score low. If it scores as high as the split arm, rule
  application is coming from the model's prior knowledge, not the supplied guidance,
  and the A/B's attribution is weak. The gap between the split and no-rule rates is
  the share of the result the guidance is genuinely responsible for.

The split arm injects the **correct** skill on purpose, so the split-vs-monolith
comparison isolates the context-size (dilution) effect from routing. Routing is
Angle 1's job. The output is a **rule-application rate** per arm (binary hits
aggregated), never a quality score. If the monolith arm exceeds the model's context
window it is recorded as `context_overflow`, which is itself evidence for the split.
For a clean dilution signal rather than hard truncation, run the monolith arm on a
large-context model.

Requires Python 3.10+ and a model access token.

```powershell
# from the repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r routing-eval/requirements.txt
```

Provide your own token (nothing is read from repo secrets):

```powershell
$env:GITHUB_TOKEN = "<your-personal-token-with-models-access>"
```

The harness defaults to **GitHub Models** (OpenAI-compatible). To point at a
different OpenAI-compatible endpoint, override these:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_TOKEN` | (required) | Your model access token |
| `ROUTING_EVAL_BASE_URL` | `https://models.github.ai/inference` | OpenAI-compatible endpoint |
| `ROUTING_EVAL_MODEL` | `openai/gpt-4o` | Model id (or use `--model`) |

---

## Run it

```powershell
# 13 split skills only (default)
python routing-eval/src/route_classify.py --arm split

# include the monolith to see how much it absorbs
python routing-eval/src/route_classify.py --arm all

# quick smoke run on the first few prompts
python routing-eval/src/route_classify.py --arm split --limit 5

# pick a specific model
python routing-eval/src/route_classify.py --arm split --model openai/gpt-4o-mini
```

### Angle 2 - rule-application A/B

```powershell
# full run (monolith vs split, all prompts)
python routing-eval/src/rule_application.py

# quick smoke run on the first 2 prompts
python routing-eval/src/rule_application.py --limit 2

# use a large-context model so the monolith arm is not truncated
python routing-eval/src/rule_application.py --model openai/gpt-4.1
```

Console shows a per-prompt `monolith=OK/XX split=OK/XX` line, then the two
rule-application rates and the list of misses. A full JSON report is written to
`routing-eval/results/` (git-ignored). To preserve a run for the team, copy that
JSON into the results notes described under [Recording results](#recording-results).

Console shows a per-prompt OK/XX line, then a summary:

```
============================================================
ROUTING EVAL  arm=split  model=openai/gpt-4o
============================================================
Overall accuracy: 92.3% (24/26)
Per-skill accuracy:
  cosmosdb-data-modeling         2/2   100%
  cosmosdb-partition-key         1/2   50%
  ...
Misroutes (expected -> selected):
  partition-002    cosmosdb-partition-key -> cosmosdb-throughput
```

A full JSON report (including the confusion matrix and every row) is written to
`routing-eval/results/` (git-ignored).

---

## Reading the results

- **Per-skill accuracy** tells you which skills are reliably found.
- **Confusion matrix** (in the JSON) shows which skill **stole** a misrouted
  prompt. If partition-key questions leak into throughput, those two descriptions
  overlap and one needs sharpening.
- Fix the `description` in the offending skill's `SKILL.md`, then re-run. You are
  tuning the routing surface, not the rules.

---

## The monolith decision

The end goal is to remove the monolith (maintaining duplicate rules in both the
monolith and a split skill is a maintenance burden). The monolith currently stays
as a safe catch-all. Retire it when:

1. **Angle 1 `--arm split`** shows per-skill routing accuracy is high across the
   corpus, and
2. The prompts the monolith absorbed in **Angle 1 `--arm all`** re-route to the
   **correct specific** skill under `--arm split`, and
3. **Angle 2** shows the split's rule-application rate is at least as good as the
   monolith's (i.e. the focused split does not lose rules the monolith applied, and
   ideally recovers rules the monolith's overloaded context was missing).

Angle 2 is the transitional confirmation that closes the loop on context overload;
it retires with the monolith. Angle 1 is permanent: until the monolith is gone, and
forever after as skills are added, run it locally before merging any change to a
skill `name` or `description`, since those edits can silently shift routing for
unrelated skills.

---

## Recording results

The raw JSON in `routing-eval/results/` is git-ignored. To preserve a run for the
team to review, summarise it in [`RESULTS.md`](RESULTS.md) (committed). That file is
the durable record behind the retire/archive decision, and it is where the Angle 2
A/B lives on for posterity after the monolith is archived. Add a dated section per
run with the model used, the headline numbers, and a short interpretation.

---

## Running in CI (intentionally not enabled)

There is a **dormant** workflow template at
[`ci/routing-eval.workflow.yml`](ci/routing-eval.workflow.yml). It is **not** in
`.github/workflows/`, so it cannot run. It exists for if/when upstream GitHub
Models access is granted to Actions. When activated it is `workflow_dispatch`-only
(never on PRs), restricted to write-access users, gated behind a required-reviewer
environment, and limited by an actor allowlist. See the comments in that file.

---

## Extending the corpus

Add entries to [`prompts/labeled-prompts.yaml`](prompts/labeled-prompts.yaml).
Useful additions:

- **Ambiguous** prompts that legitimately span two skills.
- **Out-of-scope** prompts where the right answer is to pick nothing
  (`expected_skill: none`) to catch over-triggering.

Keep prompts phrased like real questions and avoid naming the skill directly.
