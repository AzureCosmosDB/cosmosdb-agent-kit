<#
.SYNOPSIS
  Script to enable or disable ChaosFault to a CosmosDB account.
.PARAMETER ResourceGroup
  The resource group where the CosmosDB account is located.
.PARAMETER AccountName
  The DocDB account name.
.PARAMETER SubscriptionId
  The subscription id of the CosmosDB account.
.PARAMETER Region
  The preferred write region you want to Enable/Disable the Fault
.PARAMETER DatabaseName
  The databaseName of the CosmosDB account where the container is located.
.PARAMETER ContainerName
  The CollectionName where you want to enable/disable the Fault.
.PARAMETER Enable
  Attributive to enable the chaos fault.
.PARAMETER Disable
  Attributive to disable the chaos fault..
.EXAMPLE
    # 1.Enables PerPartitionAutomaticFailover fault in Region North Central US for databaseName "exampleDb" and containerName "exampleCon" in CosmosDB account "example" in resource group "example-docdb" in subscription "12341234-5678-4769-92d0-7e62eec4da60"
  .\EnableDisableChaosFault.ps1 -FaultType "PerPartitionAutomaticFailover" -ResourceGroup "example-docdb" -AccountName "example" -DatabaseName "exampleDb" -ContainerName "exampleCon"  -SubscriptionId "12341234-5678-4769-92d0-7e62eec4da60" -Region "North Central US" -Enable

   # 2.Disables PerPartitionAutomaticFailover fault in Region North Central US for databaseName "exampleDb" and containerName "exampleCon" in CosmosDB account "example" in resource group "example-docdb" in subscription "12341234-5678-4769-92d0-7e62eec4da60"
  .\EnableDisableChaosFault.ps1 -FaultType "PerPartitionAutomaticFailover" -ResourceGroup "example-docdb" -AccountName "example" -DatabaseName "exampleDb" -ContainerName "exampleCon" -SubscriptionId "12341234-5678-4769-92d0-7e62eec4da60" -Region "North Central US" -Disable
   
   # 3.Get PerPartitionAutomaticFailover fault status for CosmosDB account "example" in resource group "example-docdb" in subscription "12341234-5678-4769-92d0-7e62eec4da60" 
  .\EnableDisableChaosFault.ps1 -FaultType "PerPartitionAutomaticFailover" -ResourceGroup "example-docdb" -AccountName "example" -SubscriptionId "12341234-5678-4769-92d0-7e62eec4da60" -GetStatus
#>

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet('ServiceUnavailability','PerPartitionAutomaticFailover')]
    [string]$FaultType,

    [parameter(Mandatory=$true)]
    [ValidateNotNull()]
    [string] $ResourceGroup,

    [parameter(Mandatory=$true)]
    [ValidateNotNull()]
    [string] $AccountName,

    [parameter(Mandatory=$true)]
    [string] $SubscriptionId,

    [parameter(Mandatory=$false)]
    [string] $Region,

    [parameter(Mandatory=$false)]
    [string] $DatabaseName,

    [parameter(Mandatory=$false)]
    [ValidateNotNull()]
    [string] $ContainerName,

    [switch] $GetStatus,

    [ValidateScript({ $Disable -ne $True })]
    [switch] $Enable,

    [ValidateScript({ $Enable -ne $True })]
    [switch] $Disable
)

################################################################################################
$DebugPreference = "Continue";
$VerbosePreference = "SilentlyContinue";
$ErrorActionPreference = "Stop";


# Set Active Subscription
az account set --subscription $SubscriptionId

# Get session token
$token = az account get-access-token | ConvertFrom-Json

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = ("{0} {1}" -f $token.tokenType,$token.accessToken)
}

##################################################################################################

# Cosmos DB management API
$baseURI = ("https://management.azure.com/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}" -f $SubscriptionId,$ResourceGroup,$AccountName)
$suffixURI =  "?api-version=2024-09-01-preview"

$params = @{
    ContentType = 'application/x-www-form-urlencoded'
    Headers = $headers
}

function getStatus()
{

		$uri = $baseURI + "/ChaosFaults/PerPartitionAutomaticFailover" + $suffixURI
    $response = Invoke-WebRequest @params -Method 'Get' -Uri $uri
    echo $response.Content
}

function disable()
{

		$uri = $baseURI + "/ChaosFaults/PerPartitionAutomaticFailover" + $suffixURI
    $action = "Disable"

    $body = @"
{
      "properties": {
         "Action": "$action",
         "Region": "$Region",
         "DatabaseName": "$DatabaseName",
         "ContainerName": "$ContainerName"
      }
    }
"@
    Write-Host $body
    Write-Host $uri
    $response = Invoke-WebRequest @params -Method 'Put' -Body $body -Uri $uri
    echo $response.StatusDescription
    echo $response.Content

    $location = CanonicalizeLocation($response.Headers.Location)
    sleep 30
    $result = Invoke-WebRequest @params -Method 'Get' -Uri $location
    echo $result.StatusDescription
    echo "waiting for 15 mins to complete disabling the Fault"
    sleep 900
    $result = Invoke-WebRequest @params -Method 'Get' -Uri $location
    echo $result.StatusDescription
}

function enable()
{

		$uri = $baseURI + "/ChaosFaults/PerPartitionAutomaticFailover" + $suffixURI
    $action = "Enable"
    
    $body = @"
{
      "properties": {
         "Action": "$action",
         "Region": "$Region",
         "DatabaseName": "$DatabaseName",
         "ContainerName": "$ContainerName"
      }
    }
"@

    Write-Host $body
    Write-Host $uri
    $response = Invoke-WebRequest @params -Method 'Put' -Body $body -Uri $uri
    echo $response.StatusDescription
    echo $response.Content

    $location = CanonicalizeLocation($response.Headers.Location)
    sleep 30
    $result = Invoke-WebRequest @params -Method 'Get' -Uri $location
    echo $result.StatusDescription
    echo "waiting for 15 mins to complete enabling the Fault"
    sleep 900
    $result = Invoke-WebRequest @params -Method 'Get' -Uri $location
    echo $result.StatusDescription
}

function CanonicalizeLocation($location)
{
    if ($location.GetType().Name -eq "String[]") {
        $location = $location[0]
    }
    return $location
}


if ($Enable)
{
    enable
}
elseif ($Disable)
{
    disable($Region, $DatabaseName, $ContainerName, $FaultType)
}
elseif($GetStatus)
{
    getStatus
}