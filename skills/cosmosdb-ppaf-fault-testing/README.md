# Azure Cosmos DB PPAF service-fault testing

This is the canonical human runbook for testing **per-partition automatic
failover (PPAF)** with an existing Azure Cosmos DB account and an explicitly
approved application workload. It works across SDKs without providing a runner,
provisioning resources, or bundling the upstream script. The companion
[SKILL.md](SKILL.md) guides agents through this same procedure.

**A production fault can disrupt real traffic and incur costs. Reading this
guide, enabling the account feature, or approving a workload does not authorize
fault injection. Obtain explicit approval for the complete test and recovery.**

## Contents

- [Mechanism and prerequisites](#mechanism-and-prerequisites)
- [Approval record](#approval-record)
- [Pinned script and CLI context](#pinned-script-and-cli-context)
- [Baseline and observation gate](#baseline-and-observation-gate)
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
| Mutations | Permitted reads/writes/deletes, deterministic test IDs or namespace, data ownership, and any separately approved data cleanup |
| Timing | UTC start/end, enable deadline, active observation deadline, cleanup deadline, polling interval, and bounded retry budget |
| Criteria | Numerical availability/error, retry and latency thresholds; required regional-write/failover evidence; explicit abort conditions |
| Recovery | Exact matching disable command, independently reachable recovery operator, observation method, and escalation path |
| Ownership | Exclusive ownership of the account-level chaos fault from inactive baseline through verified cleanup |
| Consent | Approval for fault enable, disable recovery on all exit paths, workload/mutations, window, and explicit production disruption acknowledgment when applicable |

An example request is: "Prepare a PPAF test plan for my existing account and
workload; do not execute yet." That authorizes planning only. Changed targets,
workload mutations, deadlines, or broader recovery actions require renewed
approval. Test data deletion is not implicitly authorized by fault cleanup.

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

The status command is deliberately account-scoped. **Require an authoritative
known inactive baseline with no pending enable/disable operation and exclusive
account-level ownership.** An empty response, 404, permission error, unrecognized
JSON, or missing field is *unknown*, not inactive. Active or unknown baseline
blocks enable; do not disable pre-existing faults to make the test possible.

Before enable, identify and demonstrate a working, authorized observation path
that can establish **terminal operation completion and actual fault state**.
Have the service/account operator validate how the real API response or
service-side observation maps to active/inactive and pending/terminal state.
Do not invent `status`, `properties.state`, or other response paths. Preserve
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
observation path if necessary. If only HTTP descriptions or process exit codes
are available, **do not enable**. Neither a generic successful HTTP response nor
completion of the sleeps proves that the fault is active or removed.

Agree on bounded polling using the verified observation contract, including
maximum command durations, observation loss/timeout handling, and escalation.
Do not start a fault with an observer you intend to discover afterward.

Run the approved workload before injection and capture healthy baseline writes,
latency, errors/retries, and contacted regions. Verify that the workload targets
the approved container and can demonstrate affected-partition coverage. Do not
increase its load or mutate additional data to force an observable failure
without renewed approval.

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

Use terminal operation evidence **and** active fault evidence to mark the active
interval. Continue the approved workload while recording independent metrics.
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

The supervisor must initiate cleanup after success, errors (including partial
enable), workload failure, cancellation, lost observation, and enable/active
timeouts. Set a separate bounded cleanup deadline and retry budget. Stop or
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
| Contacted regions plus service write metrics | Evidence of writes in a secondary region, not merely a configured preferred region |
| Partition coverage and recovery samples | Workload exercised affected partitions and returned to the expected post-fault behavior |

The [configuration guide][configure] recommends **Total Requests** broken down
by region and **PartitionWriteGlobalStatus** for service-side evidence. Separate
write operations from reads; use SDK-specific diagnostics appropriate to the
approved version rather than inventing uniform diagnostic fields. Do not claim
data integrity from availability alone; perform only approved correctness
checks. Do not promise a universal recovery-time threshold or immediate failback.

Report two independent outcomes: **test passed / failed / inconclusive** against
the preapproved criteria, and **cleanup verified / unresolved**. Missing state,
region, partition coverage, or timing observations makes failover validation
inconclusive. Violated workload thresholds can still be reported as failures;
neither outcome excuses unresolved cleanup. A zero script exit code, successful
PUT, healthy reads, or no errors in a workload that missed the faulted partitions
cannot establish a pass.

Include scope, SDK/version, pinned source/hash, approvals, timeline, sanitized
evidence references, threshold results, deviations, CLI restoration result, and
cleanup/handoff status. Exclude secrets, authorization headers, credential
caches, raw payloads, and unsanitized debug transcripts.

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
- [Azure CLI configuration and AZURE_CONFIG_DIR](https://learn.microsoft.com/cli/azure/azure-cli-configuration)
- [Azure Cosmos DB role-based access control](https://learn.microsoft.com/azure/cosmos-db/role-based-access-control)

[configure]: https://learn.microsoft.com/azure/cosmos-db/how-to-configure-per-partition-automatic-failover
[script]: https://github.com/AzureCosmosDB/ppaf-samples/blob/84105f271ec042a016f3e69b8911edbfd80fea14/ppaf-fault-script/EnableDisableChaosFault.ps1
