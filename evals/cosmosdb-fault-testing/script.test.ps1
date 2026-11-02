$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot '../../skills/cosmosdb-fault-testing/scripts/EnableDisableChaosFault.ps1'
$expectedHash = 'cdc4727bb1ea288f1f65319261cc3780eec29b7d3e7b5b7b251404e2c5f3c25f'
if ((Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash -ine $expectedHash) {
    throw 'Bundled snapshot hash mismatch.'
}
$tokens = $null
$parseErrors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path $scriptPath), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }

# Shadow every external side effect: tests must never contact Azure or sleep.
function az {
    $global:ppafTest_azCalls.Add(($args -join ' '))
    if (($args -join ' ') -eq 'account get-access-token') {
        return '{"tokenType":"Bearer","accessToken":"offline-placeholder"}'
    }
    if (($args -join ' ') -ne 'account set --subscription test-subscription') {
        throw 'Unexpected Azure CLI invocation.'
    }
}
function sleep {
    param([int]$Seconds)
    $global:ppafTest_waits.Add($Seconds)
}
function Invoke-WebRequest {
    param($ContentType, $Headers, $Method, $Uri, $Body)
    if ($Uri -notin @($global:ppafTest_expectedUri, $global:ppafTest_operationUri)) {
        throw 'Unexpected HTTP target.'
    }
    if ($global:ppafTest_failRequest) { throw 'Simulated transport failure.' }
    $global:ppafTest_requests.Add(@{Method = $Method; Uri = $Uri; Body = $Body})
    return [pscustomobject]@{
        StatusDescription = 'OK'
        Content = '{"offline":true}'
        Headers = @{Location = [string[]]@($global:ppafTest_operationUri)}
    }
}
$global:ppafTest_expectedUri = 'https://management.azure.com/subscriptions/test-subscription/resourceGroups/test-rg/providers/Microsoft.DocumentDB/databaseAccounts/test-account/ChaosFaults/PerPartitionAutomaticFailover?api-version=2024-09-01-preview'
$global:ppafTest_operationUri = 'https://management.azure.com/offline-operation'
$scope = @{
    FaultType = 'PerPartitionAutomaticFailover'
    ResourceGroup = 'test-rg'
    AccountName = 'test-account'
    SubscriptionId = 'test-subscription'
    DatabaseName = 'test-db'
    ContainerName = 'test-container'
    Region = 'East US'
}
foreach ($mode in @('GetStatus', 'Enable', 'Disable', 'Failure')) {
    $global:ppafTest_requests = [System.Collections.Generic.List[object]]::new()
    $global:ppafTest_azCalls = [System.Collections.Generic.List[string]]::new()
    $global:ppafTest_waits = [System.Collections.Generic.List[int]]::new()
    $global:ppafTest_failRequest = $mode -eq 'Failure'
    $switches = @{}
    if ($mode -eq 'Failure') { $switches['Enable'] = $true }
    else { $switches[$mode] = $true }
    $caught = $false
    try { & $scriptPath @scope @switches *> $null }
    catch {
        if ($mode -ne 'Failure' -or $_.Exception.Message -ne 'Simulated transport failure.') { throw }
        $caught = $true
    }
    if ($global:ppafTest_azCalls.Count -ne 2) { throw "$mode did not verify expected CLI calls." }
    if ($mode -eq 'Failure') {
        if (-not $caught -or $global:ppafTest_requests.Count -ne 0) { throw 'Transport error was not surfaced.' }
    } elseif ($mode -eq 'GetStatus') {
        if ($global:ppafTest_requests.Count -ne 1 -or $global:ppafTest_requests[0].Method -ne 'Get' -or $global:ppafTest_waits.Count) {
            throw 'Status must perform one GET and no waits.'
        }
    } else {
        if ($global:ppafTest_requests.Count -ne 3 -or $global:ppafTest_requests[0].Method -ne 'Put') {
            throw "$mode must perform one PUT and two operation GETs."
        }
        $properties = ($global:ppafTest_requests[0].Body | ConvertFrom-Json).properties
        $keys = @($properties.PSObject.Properties.Name) | Sort-Object
        if (($keys -join ',') -cne 'Action,ContainerName,DatabaseName,Region') {
            throw 'Request field casing changed.'
        }
        if ($properties.Action -cne $mode -or $properties.Region -cne 'East US' -or
            $properties.DatabaseName -cne 'test-db' -or $properties.ContainerName -cne 'test-container') {
            throw 'Request target/action mismatch.'
        }
        foreach ($request in $global:ppafTest_requests.GetRange(1, 2)) {
            if ($request.Method -ne 'Get' -or $request.Uri -ne $global:ppafTest_operationUri) {
                throw 'Polling target mismatch.'
            }
        }
        if (($global:ppafTest_waits -join ',') -ne '30,900') { throw 'Snapshot wait contract changed.' }
    }
    Write-Output "PASS: $mode (mocked; no Azure access)"
}
