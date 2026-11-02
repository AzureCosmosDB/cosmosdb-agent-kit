---
name: cosmosdb-fault-testing
description: Guide approved Azure Cosmos DB fault-testing and recovery exercises by collecting inputs, selecting a supported scenario, supervising execution, and verifying cleanup. Use for Cosmos DB fault testing, resilience drills, PPAF partition failover tests, or EnableDisableChaosFault.ps1. Currently supports service-side PPAF only; not resource provisioning, account-wide failover, or SDK-local fault injection.
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.4.0"
---

# Azure Cosmos DB Fault Testing

Guide the user through the workflow below; do not send them to a README to run
the test themselves. Load only the selected scenario's reference. Ask for
missing inputs one question at a time, show a concrete plan, and distinguish
planning approval from permission to execute cloud actions.

## 1. Select the scenario

| Scenario | When to select | Required resource |
|----------|----------------|-------------------|
| PPAF | Test service-side per-partition automatic failover with an existing account and approved SDK workload | [PPAF procedure](references/ppaf.md) |

PPAF is the first supported scenario, not a generic fault mechanism. If the
request is ambiguous, ask which behavior the user wants to test. For an
unsupported scenario, explain the boundary and stop before mutations; do not
substitute account failover, local exceptions, emulator behavior, or another
fault type. Future scenarios belong in separate references with their own
prerequisites, scripts, recovery contract, and evaluations.

## 2. Collect inputs and obtain approval

Read the selected reference in full. Collect and confirm:

- Exact tenant, subscription, resource group, account, database, container,
  target region, environment (test/production), and SDK version or commit.
- Existing workload command/host, permitted mutations, data ownership,
  rate/concurrency, duration, and expected partition coverage. Do not invent
  a workload, select arbitrary resources, or provision infrastructure.
- Measured RU budget/source and stop threshold; UTC window; separate enable,
  observation, cleanup, and shutdown allowances; polling/retry limits.
- Availability/latency targets, required evidence, abort conditions, and SDK
  retry/timeout settings.
- Independent recovery operator, escalation path, exclusive account-level
  fault ownership, and exact matching cleanup command.

Include this warning in every plan, before even baseline traffic:

> Test reads, writes, queries, and approved data cleanup consume Cosmos DB RUs,
> can compete with production traffic and cause throttling, and may increase
> charges depending on throughput configuration. Monitoring delays and in-flight
> requests can overshoot stop thresholds; fault cleanup remains mandatory.

Explain that fixed provisioned capacity is not billed per request; autoscale
or separately approved capacity changes may increase charges. Feature pricing
is separate. Missing request charges are unknown, not zero or an exact bill.

Default to stopping on unhandled workload failure. Continuing after specified
transient errors requires explicit failed-operation and write-unavailability
limits and bounded unknown-charge handling. Record every failure without
silently changing retry settings or replaying an ambiguously committed write.
Continuation permission is not an availability pass threshold.

Obtain explicit approval for scope, workload/cost, fault enable, matching
cleanup on all exit paths, and deadlines. Require production-disruption
acknowledgment for production. Reconfirm changes or stale approvals after a
pause. Do not change permissions, capacity, network rules, or account features
as an implicit part of testing.

## 3. Establish readiness

Use the scenario's bundled script by default. Check its recorded SHA-256 and
inspect its limitations before any invocation. See [script provenance and
update policy](references/script-provenance.md). A hash mismatch blocks
execution; never silently replace a snapshot or bypass security warnings.
The optional download/update path requires inspection, a recorded revision/hash,
compatibility review, and explicit approval before running changed code.

Verify eligibility and feature enablement separately from fault injection.
Confirm control-plane, data-plane, and observation permissions independently.
Verify identity and CLI-context isolation/restoration, and connectivity from
the actual workload host to every required regional endpoint.

Require known inactive state, no pending transition, and exclusive ownership.
Unknown/active baseline blocks enable by default. Only the narrowly scoped
first-use exception in the PPAF reference may be proposed; generic 404s,
production, ambiguous history, or missing monitoring never qualify.

Demonstrate an authorized observer for both terminal management operations and
actual fault state before enable. Save a secret-free recovery record and arrange
independent recovery after process/host death. Keep signed operation URLs in
protected transient recovery state, not chat, ordinary logs, or source control.
Start only the approved workload and confirm a healthy baseline.

## 4. Execute, observe, and recover

Follow the selected scenario's commands without broadening the target. Record
an enable attempt as potentially applied before dispatch. Supervise deadlines
and traffic independently of blocking scripts. HTTP success, sleeps, and process
exit codes alone do not prove operation completion or cleanup.

Collect timestamped logical successes/failures, retry attempts, latency, RUs,
region/partition evidence, and management state throughout the run. Record
corroborated traffic migration separately from terminal operation completion.
Retry read-only observations only within their approved tolerance; never
replay mutations because polling failed.

On completion or abort, stop/hand off traffic as planned and perform matching
cleanup, even if the workload budget is exhausted. Resolve pending-operation
ordering before bounded cleanup retries. Do not treat a Disable 404 as removal
while Enable is pending. Require terminal operations and repeated matching
disabled state; otherwise report unresolved cleanup and escalate by the
deadline, including while awaiting input. Do not silently reset deadlines.

Restore CLI context after verified cleanup or explicit recovery handoff.
Reporting errors must not skip cleanup or consume reserved shutdown time.
Verify complete remote results rather than accepting truncated output.

## 5. Report results

Report four independent verdicts:

| Criterion | Verdict |
|-----------|---------|
| Failover | Observed / not observed / inconclusive, supported by actual application traffic and coverage |
| Availability | Passed / failed / inconclusive against separately approved targets; any surfaced error fails zero-error availability |
| Full drill | Completed / incomplete, including all prescribed intervals and recovery checks |
| Cleanup | Verified / unresolved, plus deadline met / missed / not established |

Missing evidence affects the relevant criterion, not independently established
findings. Overall success requires all mandatory criteria. Report scope, SDK,
script revision/hash, approvals, UTC timeline, sanitized evidence, deviations,
and recovery ownership. Distinguish REST actions, bundled-script execution,
and each SDK actually exercised; never imply universal certification.
