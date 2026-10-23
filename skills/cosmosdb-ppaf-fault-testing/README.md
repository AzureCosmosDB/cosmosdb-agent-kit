# Azure Cosmos DB PPAF service-fault testing

This is the canonical human runbook for testing **per-partition automatic
failover (PPAF)** with an existing Azure Cosmos DB account and an explicitly
approved application workload. It works across SDKs without providing a runner,
provisioning resources, or bundling the upstream script. The companion
[SKILL.md](SKILL.md) guides agents through this same procedure.

**A production fault can disrupt real traffic and incur costs. Reading this
guide, enabling the account feature, or approving a workload does not authorize
fault injection. Obtain explicit approval for the complete test and recovery.**

> **RU and cost warning:** The test workload's reads, writes, queries, and any
> approved data cleanup consume Azure Cosmos DB Request Units (RUs). They use
> throughput that may also serve production traffic, so the drill can cause
> contention or throttling (429s). Additional requests during retries can add
> consumption; do not assume each retry has a fixed RU charge. With fixed
> provisioned throughput, using existing capacity does not itself add a
> per-request bill, but autoscale activity or separately approved capacity
> increases can raise charges. PPAF feature pricing is separate. Approve a
> workload rate, duration, RU budget, and cost acknowledgment before starting
> **even the baseline workload**; monitor measured consumption and stop the
> workload at its agreed limit while still completing fault cleanup.
> See [Request Units and billing](https://learn.microsoft.com/azure/cosmos-db/request-units).

## Contents

- [Mechanism and prerequisites](#mechanism-and-prerequisites)
- [Approval record](#approval-record)
- [Pinned script and CLI context](#pinned-script-and-cli-context)
- [Baseline and observation gate](#baseline-and-observation-gate)
- [Observed API contract and polling](#observed-api-contract-and-polling)
- [Enable, observe, and disable](#enable-observe-and-disable)
- [Recovery and context restoration](#recovery-and-context-restoration)
- [Evidence and outcome](#evidence-and-outcome)
- [Installation and evaluation](#installation-and-evaluation)
- [References](#references)

## Mechanism and prerequisites

PPAF is **service-side partition failover**, distinct from SDK-local fault
injection, client retry mocks, and account-level manual/automatic failover.
Do not substitute those mechanisms or an emulator and claim a PPAF test passed.
The fault script targets a database/container/region, but its management fault
resource and status endpoint are **account-level**; do not assume independent
drills in different containers can safely overlap.

Follow the current [PPAF configuration prerequisites][configure]. The documented
configuration requires a NoSQL single-write account with another read region,
supported consistency and region configuration, and PPAF-capable SDKs on **all**
application instances. Check current eligibility and SDK support rather than
assuming every SDK or version is supported. For an experimental SDK, record its
exact repository/commit and obtain explicit approval for that unsupported or
experimental configuration; this guide is not a support certification.

A human can enable eligible accounts in the Azure portal at **Settings >
Features > Per-partition automatic failover**. Review prerequisites, pricing,
and the feature's availability on that account before enabling it. If the option
is missing or unavailable, stop and consult the account/service owner. Do not
automate portal changes or provision a replacement account. Account PPAF
enablement is a separate configuration change from enabling a chaos fault;
fault cleanup does **not** mean disabling the PPAF account feature.

Use PowerShell 7 and Azure CLI in an approved environment with access to public
Azure Resource Manager and the workload's Cosmos DB endpoints. The pinned
script hardcodes `management.azure.com`; do not use it for sovereign clouds.
Verify separately:

| Plane | Required capability |
|-------|---------------------|
| Control | Read the account/fault state and perform the approved chaos enable/disable operations |
| Data | Run exactly the approved application reads/writes against the chosen database/container |
| Observation | Read authoritative fault/operation state and the service metrics plus SDK diagnostics needed for the test |

Have the account administrator confirm the applicable permissions; this guide
does not invent a chaos RBAC role or grant access. Data-plane contributor access
alone does not establish control-plane permissions. Do not collect keys or
persist tokens, CLI credential caches, connection strings, or raw document
payloads in test artifacts.

## Approval record

Before any mutation, present a concrete plan and record explicit user approval.
Keep a secret-free record outside source control in an access-controlled test
location. Fill every field; no auto-selected defaults:

| Field | Required decision |
|-------|-------------------|
| Target | Exact tenant ID, subscription ID, resource group, account, database, container, and target region as configured on the account |
| Configuration | Account topology, consistency, feature eligibility/enabled state, SDK name/version or experimental commit |
| Workload | User-approved existing command, host, duration, concurrency/rate, partition coverage, and diagnostic sources |
| RU and cost budget | Approved workload RU budget and rate/duration limits, measured request-charge or service-metric source, monitoring interval and stop threshold, plus acknowledgment of production capacity contention and possible additional charges |
| Mutations | Permitted reads/writes/deletes, deterministic test IDs or namespace, data ownership, and any separately approved data cleanup |
| Timing | UTC start/end, enable deadline, active observation deadline, cleanup deadline, polling interval, and bounded retry budget |
| Criteria | Numerical availability/error, retry and latency thresholds; required regional-write/failover evidence; explicit abort conditions |
| Failure policy | SDK timeout/retry configuration; stop-on-error or explicitly allowed transient failures; maximum failed operations and time without a successful write; unknown-charge handling |
| Recovery | Exact matching disable command, independently reachable recovery operator, observation method, and escalation path |
| Ownership | Exclusive ownership of the account-level chaos fault from inactive baseline through verified cleanup |
| First-use exception | Normally none. For a dedicated test account only, record any separately authorized missing-resource exception, its evidence and uncertainty; see the baseline gate below |
| Consent | Approval for fault enable, disable recovery on all exit paths, workload/mutations, window, and explicit production disruption acknowledgment when applicable |

An example request is: "Prepare a PPAF test plan for my existing account and
workload; do not execute yet." That authorizes planning only. Changed targets,
workload mutations, deadlines, or broader recovery actions require renewed
approval. Test data deletion is not implicitly authorized by fault cleanup.
Estimate consumption from representative measured request charges and the
approved operation mix, rate, and duration, including baseline, fault, recovery,
and any approved data cleanup. Do not invent a universal RU cost or promise an
exact monetary estimate without the account's throughput/pricing configuration.
Treat a monitored budget as a stop threshold, not a guaranteed hard billing cap:
in-flight requests and metric delays can cause overshoot. Do not increase
throughput or autoscale limits without separate approval.

### Transient failures versus abort conditions

Stopping on the first unhandled workload failure remains the default. To
measure recovery through a disruption, the operator may instead explicitly
approve continuing after specified transient failures (for example, selected
timeouts or 503s) at the same rate, within a maximum failure count and maximum
time without a successful write. Record each failed logical operation,
underlying attempts when observable, latency, and the exact retry/timeout
configuration. Do not silently retry an ambiguous write, alter SDK settings,
raise traffic, or suppress errors to improve the result. An ambiguous write
may have committed; define safe verification or subsequent-operation behavior
in the approved workload rather than assuming it failed.

Any client-visible error fails a requested **zero-error availability** criterion,
even when continuation is authorized and secondary-region writes recover.
The continuation allowance controls whether observation may proceed, not
whether availability passes. Evaluate separately approved availability targets;
if none were defined, report availability as inconclusive rather than inventing
a success threshold from the abort limit.
Correctness violations, authentication failures, observation loss beyond its
approved tolerance, and RU/rate/time/failure thresholds remain abort conditions.
A timeout may hide a billable request charge: label observed RUs as incomplete,
not the billing total. Without an explicitly approved bounded policy for
unknown-charge attempts, stop traffic. Never treat missing charges as zero,
permit unlimited unknown consumption, or allow any exception to waive cleanup.

## Pinned script and CLI context

The reviewed source is [EnableDisableChaosFault.ps1 at
84105f271ec042a016f3e69b8911edbfd80fea14][script]. Do not download from a moving
branch, pipe a download into execution, or silently update the pin.

Run the following download-only commands in an approved local scratch directory
outside the repository. Inspect the file before running any of its commands:

```powershell
$revision = '84105f271ec042a016f3e69b8911edbfd80fea14'
$scriptPath = Join-Path (Get-Location) 'EnableDisableChaosFault.ps1'
if (Test-Path $scriptPath) { throw 'Choose an empty scratch directory; do not overwrite an existing script.' }
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/AzureCosmosDB/ppaf-samples/$revision/ppaf-fault-script/EnableDisableChaosFault.ps1" -OutFile $scriptPath
Get-FileHash -Algorithm SHA256 -Path $scriptPath
Get-Content -Raw -Path $scriptPath
```

Record the source revision and downloaded hash. Compare the downloaded content
to the pinned source; a locally calculated hash alone is not an independent
integrity check. Stop on unexpected content, download errors, or security
warnings; do not bypass execution policy or certificate checks.

Inspection of this revision establishes important limits:

- `FaultType` accepts `ServiceUnavailability` too, but all requests hardcode
  `/ChaosFaults/PerPartitionAutomaticFailover?api-version=2024-09-01-preview`.
  **Use only `PerPartitionAutomaticFailover`.**
- Every invocation runs `az account set --subscription`, even `-GetStatus`.
  The script does not explicitly check native Azure CLI exit codes.
- Enable and disable each issue a PUT, follow the response `Location`, sleep
  30 seconds, read once, sleep 900 seconds, then read once more. There is no
  terminal-state polling loop or dependable end-to-end deadline.
- Operation GETs print `StatusDescription`, not the full terminal operation
  body. `-GetStatus` prints the fault resource response content. Neither output
  has a documented state schema in the script.
- Preserve its request field casing: lowercase outer `properties`, then
  **`Action`, `Region`, `DatabaseName`, and `ContainerName`**. Do not replace these
  with lowercase fields from a generated API example. In the live check below,
  the lowercase request failed with `region is null or empty`; the pinned
  script's PascalCase fields were accepted. The upstream request format did
  not need fixing.
- Database, container, and region values are inserted into JSON without
  escaping. Reject values containing double quotes, backslashes, or control
  characters; do not modify the script or risk malformed/widened payloads.

Prefer a **fresh, private Azure CLI configuration directory for this drill**
and a dedicated PowerShell session. Replace all angle-bracket placeholders
below before use. Do not copy another session's credentials into this directory.
It is a credential cache, not a test artifact; secure it with local OS
permissions and do not share or commit it.

```powershell
$tenantId = '<approved-tenant-id>'
$subscriptionId = '<approved-subscription-id>'
$previousAzureConfigDir = $env:AZURE_CONFIG_DIR
$env:AZURE_CONFIG_DIR = '<new-private-absolute-directory-outside-repository>'
New-Item -ItemType Directory -Path $env:AZURE_CONFIG_DIR -ErrorAction Stop | Out-Null
az login --tenant $tenantId --output none
if ($LASTEXITCODE -ne 0) { throw 'Azure login failed.' }
az account set --subscription $subscriptionId
if ($LASTEXITCODE -ne 0) { throw 'Subscription selection failed.' }
$contextJson = az account show --output json
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify Azure context.' }
$context = $contextJson | ConvertFrom-Json
if ($context.tenantId -ne $tenantId -or $context.id -ne $subscriptionId) {
    throw 'Azure tenant/subscription mismatch; stop.'
}
```

Run only after identity/login approval as required by your environment. Ensure
the independent recovery operator has their own approved authentication and
verified context. Do not allow concurrent changes to this CLI configuration.
Reverify identity before mutations and recovery. If isolation is unavailable,
record the original tenant/subscription and secure exclusive use of that CLI
context; stop if either exclusivity or reliable restoration is unavailable.
Restoration instructions are below and also apply to setup failures.

## Baseline and observation gate

Define parameters from the approved record. These are script parameters, not a
promise of a service response schema:

```powershell
$accountScope = @{
    FaultType = 'PerPartitionAutomaticFailover'
    ResourceGroup = '<approved-resource-group>'
    AccountName = '<approved-account>'
    SubscriptionId = $subscriptionId
}
$faultScope = @{
    DatabaseName = '<approved-database>'
    ContainerName = '<approved-container>'
    Region = '<approved-target-region>'
}
& $scriptPath @accountScope -GetStatus
```

The status command is deliberately account-scoped. **Normally require an
authoritative known inactive baseline with no pending enable/disable operation
and exclusive account-level ownership.** An empty response, 404, permission
error, unrecognized JSON, or missing field is *unknown*, not inactive. Active or
unknown baseline blocks enable by default; never disable pre-existing faults
to manufacture a baseline.

**First use is a separate, explicit exception, not a new meaning for 404.** A
dedicated, non-production test account can return the resource-specific
`PerPartitionAutomaticFailover Chaos Fault Not Found` before its first
injection. A qualified account owner may explicitly authorize proceeding with
that uncertainty only after verifying the exact account and feature enablement,
exclusive fault ownership, creation/operation history with no prior fault
attempt or known pending operation, and all monitoring/recovery prerequisites.
Record that the baseline is **missing-resource / operator-authorized exception**,
not verified inactive. Generic "run it" approval is insufficient. Do not apply
this exception to production, permission failures, wrong targets, uninterpretable
responses, or any ambiguous previous fault attempt. Do not initialize a fault
with a blind Disable. An exception never waives the observer or cleanup gates.

Before enable, identify and demonstrate a working, authorized observation path
that can establish **terminal operation completion and actual fault state**.
Have the service/account operator validate how the real API response or
service-side observation maps to active/inactive and pending/terminal state.
Use the actual contract described below; do not invent `properties.state` or
assume one casing or enum representation across API versions. Preserve
sanitized observations and their provenance/timestamps, not credentials.

If a real operation URL is supplied by the service to an authorized observer,
the observer can read its full response using the following command; substitute
only a verified operation URL, never a guessed URL or untrusted host:

```powershell
$operationUrl = '<actual-service-operation-url>'
az rest --method get --url $operationUrl --output json
if ($LASTEXITCODE -ne 0) { throw 'Operation observation failed; state is unknown.' }
```

Verify HTTPS, the approved public ARM host, and association with the approved
operation/account before sending authenticated requests. The script does not
reliably expose the operation URL; arrange another authorized service
observation path if necessary. The command above reads a body; it is not a
complete observer unless the chosen tooling also exposes HTTP status and
response headers. If only HTTP descriptions or process exit codes are available,
**do not enable**. Neither a generic successful HTTP response nor completion of
the sleeps proves that the fault is active or removed.

If necessary, the operator can separately approve individual REST actions
equivalent to the pinned script so that response headers are observable. Record
that execution-method change; preserve the exact target, API version, request
casing, and recovery body. This guide does not supply a replacement runner or
claim that a REST exercise validates the script end-to-end.

Agree on bounded polling using the verified observation contract, including
maximum command durations, observation loss/timeout handling, and escalation.
Do not start a fault with an observer you intend to discover afterward.

Run the approved workload before injection and capture healthy baseline writes,
latency, errors/retries, and contacted regions. Verify that the workload targets
the approved container and can demonstrate affected-partition coverage. Do not
increase its load or mutate additional data to force an observable failure
without renewed approval.
Verify connectivity to both regional endpoints from the actual workload host.
An external IP-check service may not see the egress IP used for Cosmos DB;
use the service's firewall diagnostics and a stable approved network path.
Never chase changing addresses by opening access to all networks.
The RU/cost warning and budget approval must precede this baseline. Confirm the
approved consumption observer is working, track RU usage throughout all workload
phases, and abort the workload at the agreed budget/rate/duration or contention
threshold. Budget exhaustion does not cancel the obligation to disable and
verify removal of an attempted service fault.

## Observed API contract and polling

The [published API schema][chaos-api] describes the management resource and
long-running operation. A supervised REST check on **2026-10-22**, using
`2024-09-01-preview`, observed the following response shapes. These are scoped
observations, not a complete state enumeration or a guarantee for every
deployment. Validate differences with the service operator rather than silently
normalizing unknown values.

| Surface | Observed response | Interpretation |
|---------|-------------------|----------------|
| Enable PUT | HTTP 201, `properties.ProvisioningState: "Creating"`, `Action: 0`, `Location` and `Azure-AsyncOperation` headers | Accepted, not completed |
| Operation-result `Location` GET | HTTP 202 with `{"status":"Dequeued"}` | Pending; continue bounded polling, not an abort solely because `Dequeued` is unfamiliar |
| Fault GET while enable is pending | `ProvisioningState: "Enabling"`, `Action: 0` | Enable is still transitioning; not cleanup evidence |
| Enable result after the HTTP-202 phase | HTTP 200 with `ProvisioningState: "InProgress"`, `Action: 0` | Fault lifecycle state, not by itself a failed or pending management operation; correlate with the operation status and issued Enable |
| `Azure-AsyncOperation` GET at completion | HTTP 200 with `{"status":"Succeeded"}` | Terminal management-operation success, not proof of application failover |
| Disable result and subsequent fault GET | HTTP 200 with `ProvisioningState: "Succeeded"`, `Action: 1` | Correlated with terminal success of the issued Disable, supports verified cleanup |

The observed `Action: 0` and `Action: 1` corresponded to the explicitly issued
Enable and Disable respectively. Do not infer disabled state from
`ProvisioningState: "Succeeded"` alone, or mistake numeric zero for a missing
field. Published examples may instead show lowercase fields and string actions.
The fault-resource state and the management-operation status are distinct.

Capture both operation URLs when supplied and correlate their operation IDs
with the accepted request. Poll the exact returned URLs, honoring `Retry-After`
within approved bounds. HTTP 202 from the operation-result URL remains pending
even when its body says `Dequeued`; successful HTTP transport from the separate
status endpoint is not terminal success. Require the terminal operation result
and matching fault state before declaring terminal activation or cleanup.
An individual management GET timeout is an observation gap, not a failed
Enable or Disable. Only if the plan explicitly permits it, retry that
read-only observation within a bounded count, maximum observation gap, and
the unchanged phase deadline. Never resend a mutation because polling failed.
Explicit failure/cancellation, mismatched scope, lost observation beyond the
approved tolerance, or a phase timeout triggers the recovery plan.
Unrecognized states outside a recognized pending contract
require operator interpretation, not guessed success.

Operation URLs may contain signed query parameters. Keep the intact URLs only
in protected transient recovery state while needed, never in chat, PRs, ordinary
logs, or source control. Persist sanitized paths/operation IDs as evidence and
remove signed query material after recovery; do not strip it before polling.

## Enable, observe, and disable

**These are individual commands for an approved, supervised drill, not a
copy-and-run sequence.** Before attempting enable, persist the exact target,
parameter values, source revision/hash, recovery operator, deadlines, and fully
expanded matching disable command (not just references to session variables).
Record `enable attempted / may be applied` before dispatch. An error after a PUT
can leave the service fault enabled.

```powershell
& $scriptPath @accountScope @faultScope -Enable
```

Run the blocking invocation in a supervised process/terminal while an
independent observer enforces deadlines and watches workload/service state.
Allow for at least the script's 930 seconds of fixed sleeps per enable and
disable, plus network requests and observation time, when approving the window.
The sleeps are not a guarantee of completion. If the approved window cannot
accommodate cleanup, do not start; do not silently extend it.

Use terminal operation evidence **and** active fault evidence to mark the
confirmed post-enable observation interval. Also retain the full traffic
timeline from baseline through enable and recovery: successful secondary-region
writes can precede terminal management completion. Correlate those writes with
the exact target, issued fault, baseline topology, client diagnostics and
independent regional write metrics. Record that migration when demonstrated;
do not discard it because a controller's `active` phase has not started. It
does not prove the management operation completed, all partitions moved, or a
required post-completion observation interval was exercised.
Continue the approved workload while recording independent metrics.
The service chooses affected partitions; selecting a logical partition key
does not select a faulted partition. Lack of observable impact may mean missing
coverage, not successful failover.

After the observation interval, or on any abort condition, invoke the exact
matching recovery command under the preapproved cleanup authorization:

```powershell
& $scriptPath @accountScope @faultScope -Disable
& $scriptPath @accountScope -GetStatus
```

Disable uses the **same** subscription, account, resource group, database,
container, and region as the attempted enable. Repeated status observations and
authoritative terminal operation evidence must prove return to the inactive
baseline with no outstanding transition. Do not assume an inactive sample
proves cleanup if a prior enable is still pending.

## Recovery and context restoration

The supervisor must initiate cleanup after completion, failed or uncertain
enable attempts, cancellation, failures outside the approved transient-error
allowance, observation loss beyond its approved tolerance, and abort/deadline
thresholds. Set a separate bounded cleanup deadline and retry budget. Stop or
hand off the approved workload according to the plan; do not leave it running
unattended.

If enable is still running at abort, coordinate its termination and the
in-flight service operation with the recovery operator. Killing the local
process does **not** cancel the service operation. Avoid uncoordinated concurrent
PUTs; resolve enable/disable ordering with the authoritative observer/operator.
Do not report cleanup until all relevant operations settle and inactive state
is verified. If ordering or state cannot be established within the cleanup
deadline, mark cleanup **unresolved** and escalate with the exact recovery
command, last known observations, target, and pending operation identifiers.
Never broaden the target, disable account PPAF, or clean another owner's fault.

In the live check, Disable returned `Chaos Fault Not Found` while the earlier
Enable still returned HTTP 202 and fault GET reported `Enabling`. That 404 was
**not cleanup**. The matching Disable was accepted after the enable operation
settled. Stop the workload on abort, retain the pending operation identity,
and coordinate settlement and bounded matching cleanup with the recovery
operator. Do not issue repeated concurrent PUTs or re-enable to resolve a 404.

Reserve a full cleanup allowance after the enable phase, inside the approved
overall window. Do not reset deadlines on retries or assume an operator is
still present after a long pause. If a deadline is reached while awaiting user
input, report/escalate unresolved cleanup using the preapproved recovery path;
do not wait silently for a reply. Extensions require explicit approval before
they are relied on. A later successful read verifies state **at that time**,
not completion within a missed or unobserved deadline.

Observer and workload-reporting failures must not skip fault cleanup or consume
the reserved shutdown budget. Remote command transport success is not proof
that the command succeeded: verify its execution outcome and a complete,
structured result. Keep summaries compact, retrieve large logs separately with
completeness checks, and report truncated/invalid output as an observation gap,
not an empty successful result. A partial workload summary is not a final
operation count or RU total. These are requirements for the chosen execution
tooling, not a replacement runner supplied by this skill.

A `try/finally` can help with ordinary exceptions but cannot survive process
death, host failure, or lost sessions. Have an independently reachable operator
with the recovery record ready **before enable**, able to take over monitoring
and cleanup without the original session. Do not claim this guide implements
automatic crash recovery.

After verified cleanup or explicit handoff of unresolved recovery, restore the
original environment in the originating session:

```powershell
if ($null -eq $previousAzureConfigDir) {
    if (Test-Path Env:AZURE_CONFIG_DIR) {
        Remove-Item Env:AZURE_CONFIG_DIR -ErrorAction Stop
    }
} else {
    $env:AZURE_CONFIG_DIR = $previousAzureConfigDir
}
```

For the non-isolated fallback, restore the recorded original subscription with
`az account set --subscription '<original-subscription-id>'`, check its exit
code, and use `az account show` to verify both the original tenant and subscription.
Report restoration failure explicitly. Handle the dedicated credential cache
according to local credential-retention policy after recovery is complete; do
not delete or log out a shared context or remove recovery access prematurely.

## Evidence and outcome

Build a UTC timeline for baseline, enable attempt, confirmed active interval,
disable attempt, terminal operations, and confirmed inactive recovery. Correlate:

| Evidence | What it establishes |
|----------|---------------------|
| Service fault/operation observations | Actual active/inactive state and completed transitions, independent of script exit |
| Successful workload writes and failures | Availability under the approved rate, not just successful reads or retries |
| SDK retries, status/substatus, request latency | Recovery behavior and cost to the caller; distinguish attempts from completed operations |
| Measured request charges or service RU metrics | Workload consumption against the approved budget; disclose missing samples, attribution limits, and any overshoot rather than claiming an exact total |
| Contacted regions plus service write metrics | Evidence of writes in a secondary region, not merely a configured preferred region |
| Partition coverage and recovery samples | Workload exercised affected partitions and returned to the expected post-fault behavior |

The [configuration guide][configure] recommends **Total Requests** broken down
by region and **PartitionWriteGlobalStatus** for service-side evidence. Separate
write operations from reads; use SDK-specific diagnostics appropriate to the
approved version rather than inventing uniform diagnostic fields. Do not claim
data integrity from availability alone; perform only approved correctness
checks. Do not promise a universal recovery-time threshold or immediate failback.
Discover metric availability before the drill. If a metric is unavailable,
record the gap and agree on alternate evidence or report the relevant result
as inconclusive; do not fabricate samples. Regional metadata/health-check calls
do not demonstrate secondary-region application writes.

Report the following verdicts separately, then assess the overall drill against
the preapproved criteria:

| Criterion | Verdict and evidence |
|-----------|----------------------|
| Failover | **Observed / not observed / inconclusive**. Corroborate actual secondary-region application writes and target/partition coverage; an absent signal with insufficient coverage is inconclusive, not proof of no failover. State the demonstrated scope. |
| Availability | **Passed / failed / inconclusive** against the approved error/latency thresholds. Zero-error availability fails on any surfaced error; backend attempts and client-visible failures are not interchangeable. |
| Full drill | **Completed / incomplete**. Confirm all prescribed intervals, workload verification, and recovery checks occurred; successful traffic migration cannot fill a missing interval. |
| Cleanup | **Verified / unresolved**, plus **deadline met / missed / not established**. Correlate terminal operations, repeated matching disabled state, and timestamps independently of workload success. |

Missing state, region, coverage, or timing evidence makes the affected
criterion inconclusive; it does not invalidate other corroborated findings.
For example, an observer timeout after successful regional writes can leave
failover observed, availability failed, and the full drill incomplete.
Overall success requires every mandatory criterion to be satisfied. A zero
script exit code, successful PUT, healthy reads, or an error-free workload that
missed the faulted partitions cannot establish a pass.

Include scope, SDK/version, pinned source/hash, approvals, timeline, sanitized
evidence references, threshold results, deviations, CLI restoration result, and
cleanup/handoff status. Exclude secrets, authorization headers, credential
caches, raw payloads, and unsanitized debug transcripts.

### Live validation scope

#### 2026-10-22: baseline and control-plane check

The 2026-10-22 check used a Python 4.17.1 workload with managed identity on a
dedicated VM. A baseline sample completed 30 upserts and 30 verified point reads
and recorded 232.1 RUs; this is a measured sample, **not a reusable cost estimate**.
Individual REST enable and disable operations later both reached `Succeeded`,
and the disabled fault state was verified and reconfirmed. The VM was
deallocated afterward.

The observer initially rejected the pending `Dequeued` state and aborted the
test. No application workload ran during the active-fault interval, so
**application failover validation was inconclusive**. Cleanup was verified at
17:00 UTC, after the 16:19 UTC monitoring deadline; completion within that
deadline was not established. This run did not execute the upstream PowerShell
script end-to-end or validate another SDK. The guidance above incorporates
these limitations rather than presenting the run as a full passing drill.

#### 2026-10-23: traffic migration with separately scored failures

A subsequent dedicated-account run kept Python 4.17.1 traffic flowing with an
explicit bounded timeout/503 allowance, while retaining `retry_total=0` and
10-second request timeout settings. Client regional request records and
independent target-scoped Azure metrics corroborated **676 successful upserts
and 684 successful reads in West US 2**, following baseline writes in East US.
This established secondary-region write failover during fault injection, even
while management polling still reported a pending enable operation. Metric
counts are service requests, not necessarily distinct logical operations, and
minute buckets do not establish precise failover latency.

The client recorded **10 logical timeouts**, so zero-error availability failed.
A separate management polling timeout ended observation before the planned
post-completion interval; the full drill was incomplete. Remote stop-summary
parsing also failed, so the last observed RU snapshot was not an exact final
total. Both management operations ultimately reported success; repeated
disabled-state checks verified cleanup within the approved 25-minute cleanup
allowance and 60-minute overall window. VM deallocation was independently
verified. This is a scoped recovery result, not seamless availability, a universal
SDK behavior guarantee, or an end-to-end validation of the PowerShell script.

## Installation and evaluation

Install using `npx skills add AzureCosmosDB/cosmosdb-agent-kit`, or copy this
directory to `~/.copilot/skills/` or `~/.claude/skills/`. Ask an agent to
"prepare a PPAF fault test plan" to activate it; activation is not execution
approval.

This is a procedural skill with no `rules/` or generated `AGENTS.md`.
`npm run build:skill cosmosdb-ppaf-fault-testing` intentionally skips compilation.
The repository rule validator does not validate this skill; use skill-format
validation and review the human runbook together with the focused scenarios in
`evals/cosmosdb-ppaf-fault-testing/` in the source repository. Those scenarios
follow the repository's mock-eval format. Their descriptions define manual
behavioral rubrics; a mock `task_completed` outcome is not proof of safety or
agent compliance, and no scenario authorizes live Azure execution.

## References

- [Configure PPAF, eligibility, portal steps, test procedure and metrics][configure]
- [PPAF overview](https://learn.microsoft.com/azure/cosmos-db/per-partition-automatic-failover)
- [Pinned upstream PowerShell source][script]
- [Chaos fault API schema for the pinned API version][chaos-api]
- [Track Azure asynchronous operations](https://learn.microsoft.com/azure/azure-resource-manager/management/async-operations)
- [Azure CLI configuration and AZURE_CONFIG_DIR](https://learn.microsoft.com/cli/azure/azure-cli-configuration)
- [Azure Cosmos DB role-based access control](https://learn.microsoft.com/azure/cosmos-db/role-based-access-control)

[configure]: https://learn.microsoft.com/azure/cosmos-db/how-to-configure-per-partition-automatic-failover
[script]: https://github.com/AzureCosmosDB/ppaf-samples/blob/84105f271ec042a016f3e69b8911edbfd80fea14/ppaf-fault-script/EnableDisableChaosFault.ps1
[chaos-api]: https://github.com/Azure/azure-rest-api-specs/blob/main/specification/cosmos-db/resource-manager/Microsoft.DocumentDB/DocumentDB/preview/2024-09-01-preview/chaosFault.json
