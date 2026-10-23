---
name: cosmosdb-ppaf-fault-testing
description: Plan, supervise, and assess Azure Cosmos DB per-partition automatic failover (PPAF) service-fault tests using the pinned upstream PowerShell script and a user-approved workload in any SDK. Use for PPAF fault testing, production-account partition failover drills, or EnableDisableChaosFault.ps1; not for SDK-local fault injection, account failover, or resource provisioning.
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.3.0"
---

# Azure Cosmos DB PPAF Fault Testing

Read [README.md](README.md) in full before proposing executable commands. It is
the canonical human runbook, including the pinned source, exact commands,
supervision requirements, recovery procedure, and evidence rubric. Do not create
a runner or vendor/modify the upstream script.

## 1. Establish scope and approval

Treat this as a service-side fault, not an SDK exception simulation or an
account-wide failover. Support only `PerPartitionAutomaticFailover`: the pinned
script accepts another `FaultType` but hardcodes the PPAF endpoint.

Collect the exact tenant, subscription, resource group, account, database,
container, and target region. Record the SDK version or experimental commit,
approved workload command, data mutations and ownership, UTC window, separate
enable/observation/cleanup deadlines, success thresholds, abort criteria, and
named recovery operator. Do not select resources, invent a workload, or treat
this documentation request as authorization to execute.

Separate the approved transient-error allowance from abort conditions. Default
to stopping on an unhandled workload failure unless the operator explicitly
approves recording specified failures while continuing at the same bounded
rate. Record SDK timeout/retry settings, maximum failed operations, maximum
time without a successful write, and treatment of unknown request charges.
Continuation permission is not an availability pass threshold; evaluate the
separately approved availability criteria or report that verdict inconclusive.
Never silently increase retries, hide failures, or relax correctness,
authentication, observation, RU, or cleanup safeguards to obtain a pass.

Include this customer-facing warning in every test plan **before the baseline
workload stage**, even when cost approval is already recorded:

> This test's reads, writes, queries, and approved data cleanup consume Cosmos DB
> RUs, can compete with production traffic and cause throttling, and may increase
> charges depending on your throughput configuration. We will enforce the
> approved workload stop thresholds; monitoring delays and in-flight requests
> can still cause overshoot, and fault cleanup remains mandatory.

Explain that fixed provisioned capacity
is not billed per request, but autoscale activity or separately approved
capacity changes can raise charges; PPAF feature pricing is separate. Obtain
approval for rate/duration limits, an RU budget, its measured observation source
and stop threshold, and the cost/capacity impact. Use measured request charges
for estimates, not a fixed RU-per-operation or retry assumption. Explain that
monitoring delays and in-flight requests can overshoot the threshold; do not
promise a hard spending cap or change throughput without separate approval.

Verify account eligibility and PPAF enablement separately from fault injection.
Direct the human to the portal **Settings > Features > Per-partition automatic
failover** when eligible; do not automate the portal, provision resources, change
roles, or enable account features. Confirm control-plane fault permissions,
data-plane workload permissions, and monitoring access separately. Do not assume
a data contributor role permits chaos operations or that an unlisted SDK supports
PPAF.

Present the concrete plan and obtain explicit approval for the target, workload,
fault enable and disable recovery, deadlines, and production disruption. Require
an explicit production acknowledgment for a production account. Reconfirm if any
approved scope changes. Planning can continue without execution approval.

## 2. Prove readiness before enable

Download and inspect the exact pinned upstream source from the runbook; do not
use `main`, bypass warnings, or silently substitute another revision. Isolate
Azure CLI configuration and verify tenant/subscription identity. The script
changes the active subscription even for status reads.
Preserve the script's JSON field casing: outer `properties`, then `Action`,
`Region`, `DatabaseName`, and `ContainerName`. Do not substitute lowercase
generated-schema examples. A separately approved equivalent REST execution
must capture operation headers and be reported as REST testing, not validation
of the script end-to-end.

Use account-level `-GetStatus` and authoritative service observations to establish
a **known inactive baseline with no pending transition**. Obtain exclusive
account-level fault ownership through cleanup. Active, unknown, inaccessible, or
uninterpretable status blocks enable by default; never disable someone else's
fault to manufacture a baseline. The README's dedicated-test-account first-use
exception requires explicit qualified account-owner consent, scoped history
with no prior attempt or known pending operation, and all observation/recovery
gates. Record missing-resource uncertainty rather than calling a 404 inactive.
Never extend that exception to production, generic errors, or ambiguous history.

Validate the real response contract with the operator/service documentation.
Require an available observer for terminal operation state and actual fault
state, with bounded polling and an escalation path. HTTP success, process exit,
elapsed waits, or a guessed response property is not proof. If the available
tools cannot provide these observations, stop before enable.
Read the README's observed-contract table: an operation-result `Location` GET
returning HTTP 202 with `status: Dequeued` is pending, not grounds to abort solely
for that label. Keep fault-resource `ProvisioningState` distinct from the
management-operation `status`. Correlate actual response casing and numeric or
string actions with the issued command; zero is not a missing action.
Record corroborated secondary-region writes even if the management operation
is still pending. This is traffic-migration evidence, not proof of terminal
enable completion or the prescribed post-completion observation interval.
Protect intact signed operation URLs only as transient recovery state; never
print or publish their query parameters. Retain sanitized operation IDs.

Start only the approved workload and capture its healthy baseline. Persist a
secret-free recovery record, including the exact matching disable command,
**before attempting enable**, and arrange independent supervision if the session
or process dies. Mark the enable as potentially applied as soon as attempted,
even if the command later throws or times out.
Verify the actual workload host can reach both regional endpoints; do not assume
an external IP-check service identifies Cosmos DB egress or broaden firewalls
to work around changing addresses.

## 3. Supervise and recover

Execute only the approved commands from the runbook. Keep control-state
observation and workload evidence independent of the script's fixed sleeps.
Do not let a blocking script prevent deadline or abort handling.
Monitor workload RU consumption across baseline, fault, and recovery. Stop the
workload at its approved budget or contention threshold, but still perform
fault cleanup. Record consumption, observation gaps, and any budget overshoot.

On completion, cancellation, any failure outside the approved transient-error
allowance, or an abort/deadline threshold, use the preapproved matching disable
recovery and verify terminal completion plus the known inactive baseline.
Record every allowed error while continuing observation; zero-error availability
fails on any client-visible error even if writes recover. Unknown charges are
not zero RU and require the explicitly approved bounded accounting policy.
Handle an in-flight enable/disable race with the
service operator; never infer cleanup from a single inactive sample while an
enable is pending. A Disable 404 while Enable is pending is not cleanup: retain
the operation identity, resolve ordering, then retry only the matching cleanup
within its budget. Do not re-enable or loop concurrent PUTs.
Bound cleanup retries and escalate immediately when the cleanup deadline
expires, including while awaiting user input. Reserve cleanup time after
enable within the overall window; never reset deadlines silently. Reconfirm
operator availability and approvals after a pause. Do not broaden scope or
disable account PPAF.

Restore the CLI context after cleanup or explicit recovery handoff. A `finally`
block cannot guarantee cleanup after process death, host failure, or a lost
session. Report unresolved cleanup prominently; never imply a killed process
removed the service fault.

## 4. Assess and report

Correlate timestamped baseline, active-fault, and recovery intervals with
successful writes, failures/status/substatus, retries, latency, contacted
regions, and service-side region/partition metrics. Distinguish successful
requests from retry attempts, and read traffic from writes. Require evidence
that the approved workload exercised affected partitions; do not infer coverage
from one successful write or one chosen partition key.

Report four separate verdicts: **failover observed / not observed /
inconclusive**, **availability passed / failed / inconclusive** against approved
thresholds (explicitly score zero-error availability when requested),
**full drill completed / incomplete**, and **cleanup verified / unresolved**
with deadline compliance. Missing evidence makes the affected criterion
inconclusive, not every independently established result. A later observer
failure does not erase corroborated traffic migration, but cannot validate an
unobserved interval or cleanup. Pass the overall drill only if all required
criteria are satisfied. Include the pinned
revision/hash, scope, approvals, UTC timeline, observer provenance, deviations,
and escalation owner without credentials, raw payloads, or token-bearing logs.
Discover service metric availability rather than assuming every metric exists.
No workload evidence during fault injection means application failover is
inconclusive even when both management operations succeed. A later cleanup confirmation does
not establish that the approved deadline was met. Distinguish REST checks,
script execution, and each SDK actually exercised.
