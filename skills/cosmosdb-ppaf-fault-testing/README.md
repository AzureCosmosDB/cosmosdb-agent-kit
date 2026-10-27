# Azure Cosmos DB PPAF fault testing

Use this runbook with [SKILL.md](SKILL.md) to test **per-partition automatic
failover (PPAF)** on an existing account with an approved workload in any
supported SDK. This is a service-side partition fault, not SDK-local injection,
an emulator test, or account-wide failover. No runner or upstream script is bundled.

> **RU and cost warning:** Baseline, fault, recovery, and data-cleanup requests
> consume RUs and can compete with production traffic or cause throttling.
> Fixed provisioned capacity is not billed per request, but autoscale or approved
> capacity increases can raise charges; PPAF pricing is separate. Obtain cost
> acknowledgment and rate, duration, and measured-RU stop limits before traffic
> starts. Monitoring delays and in-flight requests can overshoot those limits.

## Contents

- [Prerequisites and approval](#prerequisites-and-approval)
- [Prepare the script and CLI context](#prepare-the-script-and-cli-context)
- [Check the baseline](#check-the-baseline)
- [Enable and observe](#enable-and-observe)
- [Disable and recover](#disable-and-recover)
- [Report results](#report-results)
- [Installation and references](#installation-and-references)

## Prerequisites and approval

Follow the current [PPAF eligibility and SDK requirements][configure]: a
supported NoSQL single-write configuration with another read region and
PPAF-capable SDKs on all application instances. An experimental SDK requires
explicit approval of its exact version/commit; this guide does not certify it.
A human enables eligible accounts through **Settings > Features >
Per-partition automatic failover** in the portal after reviewing pricing.
Stop if unavailable; do not provision resources or automate feature changes.

Use PowerShell 7 and Azure CLI with public Azure Resource Manager access.
The pinned script targets `management.azure.com`, not sovereign clouds.
Verify control-plane fault permissions, data-plane workload permissions, and
monitoring access separately. Verify both regional data endpoints from the
actual workload host; external IP-check services may see different egress.
Use an approved stable network path, not an all-networks firewall workaround.

Record explicit approval for the complete plan:

| Item | Required details |
|------|------------------|
| Target | Tenant, subscription, resource group, account, database, container, and region |
| Workload | Existing command/host, SDK version, rate/concurrency, duration, partition coverage, permitted mutations and data ownership |
| Limits | RU measurement source/budget, polling interval, UTC window, separate enable/observation/cleanup deadlines, and shutdown allowance |
| Criteria | Availability/latency targets, failover evidence, abort thresholds, and SDK retry/timeout settings |
| Recovery | Exact matching disable command, independent recovery operator, escalation path, and exclusive account-level fault ownership through cleanup |
| Consent | Enable plus disable recovery, workload/cost acknowledgment, and explicit production-disruption acknowledgment when applicable |

Changes to scope or limits require renewed approval. Data deletion, capacity
changes, and disabling the account's PPAF feature are not implicit cleanup.

Default to stopping on an unhandled workload failure. Continuing after specified
timeouts/503s requires explicit maximum failure counts, time without successful
writes, and a bounded unknown-charge policy. Record every failure without
silently changing retries, replaying an ambiguously committed write, or raising
traffic. Correctness/authentication failures and exhausted limits still abort.
Continuation permission is **not** an availability pass threshold. Missing
request charges are unknown, not zero; without an approved bounded policy,
stop traffic. Estimate RU usage from measured requests, not universal costs.

## Prepare the script and CLI context

Download [the pinned upstream script][script] into an empty scratch directory
outside the repository. Inspect it before execution; do not use a moving branch,
vendor/modify the script, or bypass certificate/security warnings.

```powershell
$revision = '84105f271ec042a016f3e69b8911edbfd80fea14'
$scriptPath = Join-Path (Get-Location) 'EnableDisableChaosFault.ps1'
if (Test-Path $scriptPath) { throw 'Choose an empty scratch directory.' }
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/AzureCosmosDB/ppaf-samples/$revision/ppaf-fault-script/EnableDisableChaosFault.ps1" -OutFile $scriptPath
Get-FileHash -Algorithm SHA256 -Path $scriptPath
Get-Content -Raw -Path $scriptPath
```

Record the revision/hash and compare content against the pinned source.
The script has these constraints:

- Use only `PerPartitionAutomaticFailover`: all endpoints hardcode that fault,
  despite the parameter accepting another value.
- Preserve JSON casing: outer `properties`, then `Action`, `Region`,
  `DatabaseName`, and `ContainerName`; do not substitute generated-schema casing.
- Names are interpolated into JSON without escaping. Reject double quotes,
  backslashes, and control characters in database/container/region values.
- Every invocation changes the active Azure CLI subscription, including status.
  The script does not explicitly check native CLI exit codes.
- Enable and disable each sleep 30 + 900 seconds and print limited operation
  output. Those waits and a zero exit code do not establish completion.

Use a fresh private CLI directory and dedicated PowerShell session. Replace all
placeholders with approved values; do not copy credentials from another context.

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

Reverify identity before mutations and recovery. The recovery operator needs
independent authorized access. If isolation is unavailable, require exclusive
CLI-context use and record the original tenant/subscription for restoration.
Never put credential caches, keys, tokens, or raw document payloads in evidence.

## Check the baseline

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

The fault resource/status is **account-level**; do not assume separate containers
can run independent drills. Normally require verified inactive state, no pending
transition, and exclusive fault ownership. Empty, unauthorized, unrecognized,
or 404 responses are unknown, not inactive. Never disable another owner's fault.

**First-use exception:** Only a qualified account owner may explicitly accept a
resource-specific `PerPartitionAutomaticFailover Chaos Fault Not Found` on a
dedicated non-production account, after verifying target/feature, exclusive
ownership, history with no prior fault attempt or known pending operation, and
all observer/recovery prerequisites. Record *missing-resource / authorized
exception*, not inactive. Generic approval, production, permission errors, or
ambiguous prior activity do not qualify. Do not initialize with a blind Disable.

Demonstrate a working observer for terminal management operations **and** actual
fault state before enabling. Stop if unavailable. Start the approved workload,
verify a healthy baseline, and collect RU, error, latency, and regional evidence.

## Enable and observe

Before attempting Enable, save expanded target values, the matching Disable
command, deadlines, and recovery ownership. Mark the attempt as potentially
applied before dispatch; an exception after a PUT does not undo it.

```powershell
& $scriptPath @accountScope @faultScope -Enable
```

Supervise independently of the blocking script. Budget its fixed waits plus
network/observation time and a full cleanup allowance. Do not extend deadlines
silently. Separately approved equivalent REST actions can expose response
headers, but must preserve target/API version/casing and are not script
end-to-end validation.

### Operation polling

Use the [API contract][chaos-api] and verify the deployment's actual responses.
Capture the service-returned `Location` and `Azure-AsyncOperation` when supplied;
verify HTTPS, ARM host, target scope, and correlated operation IDs. Never guess
operation URLs. A body read alone is insufficient without HTTP status/headers:

```powershell
$operationUrl = '<actual-verified-service-operation-url>'
az rest --method get --url $operationUrl --output json
if ($LASTEXITCODE -ne 0) { throw 'Operation observation failed; state is unknown.' }
```

- HTTP 202 from the result URL is pending, including a `Dequeued` body.
  Honor `Retry-After` within approved deadlines; do not resend Enable.
- Management-operation `status` is distinct from fault-resource
  `ProvisioningState`. Correlate both with the issued action. Do not interpret
  `Succeeded` alone as disabled or numeric `Action: 0` as missing.
- For responses using PascalCase/numeric actions, correlate `Action: 0` with
  the issued Enable and `Action: 1` with Disable. An enabled fault may report
  `InProgress` after management completion. Verify alternate casing/values with
  the operator rather than silently normalizing an unfamiliar contract.
- Require terminal operation evidence and matching fault state for completion.
  A GET timeout is an observation gap: only preapproved bounded read-only
  retries are allowed. Failure/cancellation, scope mismatch, or observation
  loss beyond tolerance triggers recovery, not mutation replay.

Keep signed operation URLs in protected transient recovery storage accessible
to the recovery operator until cleanup is verified. Never publish their query
parameters; retain sanitized operation IDs and remove signed material afterward.

Record traffic throughout enable and recovery. Corroborated secondary-region
application writes can precede terminal enable completion; preserve that
evidence without claiming the required post-completion interval ran. The
service chooses affected partitions; one chosen key does not establish coverage.

## Disable and recover

After observation or any abort, perform the preapproved matching cleanup:

```powershell
& $scriptPath @accountScope @faultScope -Disable
& $scriptPath @accountScope -GetStatus
```

Use the exact same scope as Enable. Verify terminal operation completion and
repeated matching disabled state with no outstanding transition. A Disable 404
while Enable is pending is **not cleanup**: stop/hand off workload as planned,
retain the operation identity, coordinate settlement, then retry only matching
cleanup within its approved budget. Do not issue concurrent PUT loops or re-enable.

Reserve cleanup time after enable settlement and shutdown time within the
overall window. Abort on exceeded workload/observation limits, but never skip
fault cleanup because the RU budget is exhausted. Escalate unresolved recovery
at its deadline, even while waiting for user input. A later verification does
not prove the original deadline was met.

Process death cannot be handled by `finally` alone: the independent operator
must have recovery instructions and access before enable. Reporting failures
must not prevent cleanup or consume shutdown time. Validate remote execution
outcomes and complete structured output; truncated summaries are gaps, not
successful empty results or exact final RU totals.

After verified cleanup or explicit unresolved-recovery handoff, restore context
(also handle setup failures):

```powershell
if ($null -eq $previousAzureConfigDir) {
    if (Test-Path Env:AZURE_CONFIG_DIR) {
        Remove-Item Env:AZURE_CONFIG_DIR -ErrorAction Stop
    }
} else {
    $env:AZURE_CONFIG_DIR = $previousAzureConfigDir
}
```

If using a non-isolated context, restore the recorded subscription with
`az account set --subscription '<original-subscription-id>'`, check exit status,
and verify both tenant and subscription with `az account show`. Report failures.
Retain recovery credentials until recovery completes; follow local retention
policy afterward rather than deleting or logging out shared contexts.

## Report results

Correlate UTC timestamps, successful writes/verified reads, client-visible
failures, retry attempts, latency, measured RUs, contacted regions, and service
metrics. Discover availability of **Total Requests** by region/operation and
**PartitionWriteGlobalStatus**; missing coverage is a gap, not invented evidence.
Metadata/health-check traffic does not prove application writes. Perform only
approved correctness checks; do not promise universal recovery time or failback.

| Criterion | Verdict |
|-----------|---------|
| Failover | Observed / not observed / inconclusive, with corroborated secondary writes and demonstrated target/partition coverage |
| Availability | Passed / failed / inconclusive against separately approved targets; any surfaced error fails zero-error availability |
| Full drill | Completed / incomplete, including prescribed intervals and recovery checks |
| Cleanup | Verified / unresolved, plus deadline met / missed / not established |

An observer failure does not erase independently corroborated traffic migration,
but cannot fill an unobserved interval. Overall success requires all mandatory
criteria. Include scope, SDK/version, script revision/hash, approvals, sanitized
evidence, deviations, and context restoration. Unknown RU charges are not zero,
and incomplete samples are not a final billing total.

## Installation and references

Install with `npx skills add AzureCosmosDB/cosmosdb-agent-kit`, or copy this
directory to `~/.copilot/skills/` or `~/.claude/skills/`. Activating the skill is
not execution approval. This procedural skill has no generated `AGENTS.md`;
explanation-only Vally scenarios live in `evals/cosmosdb-ppaf-fault-testing/eval.yaml`.
Offline lint checks structure; executing the model-backed activation and
correctness graders is separate and does not authorize Azure fault injection.

- [PPAF requirements, configuration, and metrics][configure]
- [Pinned upstream script][script]
- [Chaos fault API schema][chaos-api]
- [Azure asynchronous operations](https://learn.microsoft.com/azure/azure-resource-manager/management/async-operations)
- [Request Units and billing](https://learn.microsoft.com/azure/cosmos-db/request-units)
- [Azure CLI configuration](https://learn.microsoft.com/cli/azure/azure-cli-configuration)
- [Cosmos DB role-based access control](https://learn.microsoft.com/azure/cosmos-db/role-based-access-control)

[configure]: https://learn.microsoft.com/azure/cosmos-db/how-to-configure-per-partition-automatic-failover
[script]: https://github.com/AzureCosmosDB/ppaf-samples/blob/84105f271ec042a016f3e69b8911edbfd80fea14/ppaf-fault-script/EnableDisableChaosFault.ps1
[chaos-api]: https://github.com/Azure/azure-rest-api-specs/blob/main/specification/cosmos-db/resource-manager/Microsoft.DocumentDB/DocumentDB/preview/2024-09-01-preview/chaosFault.json
