# Routing Eval - Results

Durable record of routing-eval runs. The raw JSON under `results/` is git-ignored;
this file is the committed summary the team reviews before deciding whether to
retire and archive the monolith skill.

Add a dated section per run: the angle, the model, the headline numbers, and a short
interpretation. Keep the Angle 2 (rule-application A/B) entries here for posterity;
they are the evidence behind the monolith decision and will remain meaningful after
the monolith is archived even though the test itself goes dormant.

---

## How to read these

- **Angle 1 (skill routing):** overall and per-skill accuracy that the right skill
  is selected from names + descriptions alone. Higher is better. Misroutes point at
  overlapping descriptions to sharpen.
- **Angle 2 (rule-application A/B):** the rule-application rate in the monolith arm
  (full overloaded context) vs the split arm (focused skill). If the split rate is
  at least as high as the monolith rate, the split is not losing rules; if it is
  higher, the focused context is recovering rules the monolith was burying.

---

## Runs

<!--
Template for a new entry:

### YYYY-MM-DD - Angle 2 rule-application A/B
- Model: openai/gpt-4.1
- Prompts: 13 (one per skill)
- Monolith rule-application rate: XX% (n/13)
- Split rule-application rate:    YY% (m/13)
- Context overflow on monolith arm: k prompt(s)
- Interpretation: <1-3 sentences on what this implies for retiring the monolith>
- Raw report: results/rule-application-<timestamp>.json (local, not committed)

### YYYY-MM-DD - Angle 1 routing
- Model: openai/gpt-4o
- Arm: split
- Overall accuracy: ZZ% (n/26)
- Notable misroutes: <expected -> selected>
- Interpretation: <...>
-->

### 2026-06-19 - Test basis changed (made the suite able to fail)

A reviewer flagged that first-pass 100% results invite false-positive suspicion.
Before the runs below, both tests were deliberately hardened so they can produce a
failing result, and a separate control was run to prove the judge discriminates:

- **Judge discrimination control (Angle 2).** Fed the judge three deliberately
  contradicting answers and three conforming answers across three rules. Result:
  0/3 false positives, 0/3 false negatives. The judge rejects answers that violate
  a rule and accepts answers that embody it, so the "applied" verdict is not a
  rubber stamp. (Throwaway script, not committed.)
- **Angle 2 gained a wrong-context (no-rule) control arm.** Each prompt now also
  runs against an unrelated skill that does NOT contain the governing rule
  (`pick_wrong_skill`). If that arm scored as high as the split arm, rule application
  would be coming from the model's prior knowledge rather than the supplied guidance.
  A low no-rule rate is the evidence the guidance is doing work. (It is reported as
  the `no-rule` arm in the harness output, kept distinct from the monolith, which is
  the everyday-sense baseline the split is compared against.)
- **Angle 1 gained adversarial prompts.** Added three ambiguous prompts that
  legitimately span two skills (scored with a new `also_acceptable` set so a
  reasonable alternate route is not punished) and three out-of-scope prompts whose
  correct answer is `none` (to catch over-triggering). Corpus grew 26 -> 32.

These changes mean a regression (a bad description, a removed rule, an
over-triggering router, or a model that only parrots context) would now show up as
a sub-100% number, where before the corpus could effectively only pass.

### 2026-06-19 - Angle 1 routing (split arm, hardened corpus)

- Model: `gpt-4.1-mini` via Azure OpenAI
- Arm: split (the 13 topic skills, no monolith)
- Prompts: 32 (two per skill + 3 ambiguous + 3 out-of-scope `none`)
- Overall accuracy: **100% (32/32)**, every skill at 100%, `none` 3/3
- Notable misroutes: none
- Interpretation: the hardened corpus can now fail in two new ways and did not. The
  three out-of-scope prompts all correctly returned `none` (no over-triggering), and
  the three ambiguous prompts all resolved to their primary expected skill (the
  `also_acceptable` alternates were not even needed). Routing therefore still adds no
  penalty, now against a corpus that includes contention and out-of-scope traffic.
  Re-run whenever a skill is added or a description changes.
- Raw report: `results/routing-split-20260619T172948Z.json` (local, not committed)

### 2026-06-19 - Angle 2 rule-application A/B (with no-rule control)

- Model: `gpt-4.1-mini` via Azure OpenAI (large input; required for the monolith arm)
- Prompts: 18 (13 single-rule + 4 multi-rule + 1 ambiguous)
- Monolith rule-application rate: **100% (18/18)**
- Split rule-application rate: **100% (18/18)**
- No-rule (wrong-context) rate: **72.2% (13/18)** — lower is better here
- Context overflow on monolith arm: 0 (on Azure)
- No-rule misses (rule NOT applied when the governing rule was absent from context):
  `ra-vector-001` (vector-index-type), `ra-fts-001` (fts-enable-capability),
  `ra-sdk-multi-001` (singleton + retry-429), `ra-partition-multi-001`
  (avoid-hotspots + hierarchical), `ra-security-multi-001` (disable-local-auth +
  network-restrict + rbac-least-privilege).

**Interpretation.** The no-rule arm is the important new signal. With the governing
rule removed from context, rule application drops from 100% to 72.2%, so roughly a
quarter of the corpus is genuinely carried by the supplied guidance rather than the
model's prior knowledge. Crucially, the harness is therefore NOT pinned at 100%: it
produced five sub-pass cases under the no-rule condition, which answers the
false-positive concern. The five misses cluster on niche features (vector, full-text
search) and multi-rule completeness (SDK, partition, security), which is exactly
where a model's generic Cosmos DB knowledge is thinnest and the skill content adds
the most. The flip side, recorded honestly: on the other ~72% `gpt-4.1-mini` already
knew the practice, so on a capable large-context model the skill's marginal quality
contribution is concentrated in those niche/multi-rule cases rather than spread
evenly. Split vs monolith remains at parity (100% / 100%); the case for the split
still rests on the structural and operational advantages, not a measured quality gap.

- Raw report: `results/rule-application-20260619T173643Z.json` (local, not committed)

### 2026-06-19 - Angle 1 routing (split arm)

- Model: `gpt-4.1-mini` via Azure OpenAI
- Arm: split (the 13 topic skills, no monolith)
- Prompts: 26 (two per skill)
- Overall accuracy: **100% (26/26)**, every skill 2/2
- Notable misroutes: none
- Interpretation: from skill names + descriptions alone, the router selects the
  correct skill for every labeled prompt. The split's descriptions are currently
  unambiguous enough that routing introduces no penalty on this corpus, so the
  routing-vs-focus trade-off nets out in the split's favour (no routing loss, and
  the structural/operational gains stand). Re-run this whenever a skill is added or
  a description changes.
- Raw report: `results/routing-split-20260619T171757Z.json` (local, not committed)

### 2026-06-19 - Angle 2 rule-application A/B (expanded corpus: ambiguous + multi-rule)

- Model: `gpt-4.1-mini` via Azure OpenAI (large input; required for the monolith arm)
- Prompts: 18 (13 single-rule + 5 dilution-stress: 4 multi-rule, 1 ambiguous)
  - Multi-rule prompts require EVERY listed rule to be applied to count as a hit
    (e.g. `ra-security-multi-001` needs all of disable-local-auth, network-restrict,
    rbac-least-privilege). All rules in a multi-rule prompt stay within one skill so
    the split arm has every needed rule and the A/B isolates dilution from routing.
- Monolith rule-application rate: **100% (18/18)**
- Split rule-application rate: **100% (18/18)**
- Context overflow on monolith arm: 0 (on Azure)

**Interpretation.** Parity holds even under the harder corpus. The ambiguous
query-vs-index prompt and the multi-rule modeling, SDK, partition, and security
prompts were all applied correctly by both arms. `gpt-4.1-mini` surfaced the right
two or three governing rules out of 100+ in the full monolith context just as
reliably as out of the focused split, so we still observe **no dilution gap** on this
model. The conclusion sharpens: with a capable large-context model, the split causes
no quality regression even when several specific rules must be retrieved from a
crowded context. A dilution benefit, if it exists, would require a weaker or
smaller-context model; the case for the split therefore rests on the structural and
operational advantages below, not on a measured quality delta.

- Raw report: `results/rule-application-20260619T165225Z.json` (local, not committed)

### 2026-06-19 - Angle 2 rule-application A/B (initial pass)

- Model: `gpt-4.1-mini` via Azure OpenAI (large input; required for the monolith arm)
- Prompts: 13 (one per skill, each with one clear governing rule)
- Monolith rule-application rate: **100% (13/13)**
- Split rule-application rate: **100% (13/13)**
- Context overflow on monolith arm: 0 (on Azure)

**Interpretation.** Parity. The focused split applied every governing rule the
full-context monolith did, so splitting causes no quality regression on this corpus.
We did **not** observe a dilution benefit here: `gpt-4.1-mini` handled the full
~125k-token monolith without misses, so the focused context did not need to "rescue"
any rule. This is necessary-but-not-sufficient evidence to retire the monolith on
quality grounds. Dilution effects are most likely to appear on ambiguous prompts
(where competing rules contend) or on weaker / smaller-context models, neither of
which this pass stresses. Suggested next steps before a retire decision: add
ambiguous and multi-rule prompts, and repeat on a model more prone to long-context
dilution.

**Operational finding (independent of dilution).** The monolith arm (~125k tokens)
exceeds GitHub Models' ~16k input cap (`413 tokens_limit_reached`) and can only be
submitted to a large-input endpoint such as Azure OpenAI. The split skills (each
roughly 4k to 18k tokens) load fine anywhere. The monolith being too large to load
as a single context on a capped endpoint is itself an argument for the split for any
flat-load consumer.

**Corpus correction during the run.** `ra-global-001` was first labeled with
`global-multi-region`; the prompt is about read latency for distributed users, so the
correct governing rule is `global-read-regions`. After relabeling, both arms scored
100%. (The judge correctly flagged the original mismatch in both arms, which is a good
sign the rule-application check is discriminating, not rubber-stamping.)

- Raw report: `results/rule-application-20260619T164129Z.json` (local, not committed)

---

_Add new runs above this line._

---

## Addendum: the endpoint input cap is an indictment of the monolith

This deserves to be called out separately from the A/B numbers, because it is true
regardless of how any quality comparison turns out.

**What happened.** The monolith arm could not run on GitHub Models at all. The
monolith's compiled `AGENTS.md` is ~125k tokens, and GitHub Models rejects any
request whose body exceeds ~16k input tokens (`413 tokens_limit_reached`,
`Max size: 16000 tokens`). The A/B only completed because we pointed the monolith
arm at an Azure OpenAI deployment with a large input limit. The split skills, at
roughly 4k to 18k tokens each, loaded without issue on either endpoint.

**Why this is an indictment of keeping everything in one monolith skill.** A skill
is supposed to be loadable by the agents that consume it. A 125k-token single file:

- Cannot be loaded as one context by input-capped hosted endpoints (GitHub Models,
  and any tier or gateway with a similar cap). The artifact is simply unusable there.
- Forces reliance on premium large-context models even when the task only needs one
  small topic's rules, wasting context budget and money on 100+ irrelevant rules.
- Pushes every flat-load (non-progressive) consumer to ingest the entire ruleset to
  get any single rule, which is the opposite of context efficiency.

**Why this endorses the split.** Each split skill is small enough to load anywhere,
including capped endpoints, and a routing agent pulls in only the relevant topic.
The split turns an artifact that is too big to load into a set of artifacts that
always load, while carrying the identical rule content. That benefit is structural
and permanent. It does not depend on a measured dilution effect, and it stands even
though this pass showed answer-quality parity rather than a dilution gap.

**Bottom line.** Even with quality parity (100% vs 100% on this corpus), the monolith
is the worse artifact to ship: it is too large to load on common endpoints, while the
split loads everywhere and costs less context per task. The cap finding alone is a
strong, model-independent argument for retiring the monolith in favour of the split.
