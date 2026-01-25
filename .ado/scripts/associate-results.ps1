
param(
  [Parameter(Mandatory=$true)][string]$Organization, # e.g., https://dev.azure.com/contoso/
  [Parameter(Mandatory=$true)][string]$Project,      # e.g., Fabrikam
  [Parameter(Mandatory=$true)][string]$BuildId,
  [Parameter(Mandatory=$true)][string]$MappingFile
)


$token = $env:SYSTEM_ACCESSTOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Error "System.AccessToken is not available. Make sure persistCredentials: true is set."
    exit 1
}

$authHeaders = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}


# 1) Load mapping: testCaseId -> path
$map = (Get-Content $MappingFile -Raw | ConvertFrom-Json).mappings
$pathToCase = @{}
foreach ($m in $map) { $pathToCase[$m.path] = [int]$m.testCaseId }

# 2) Find the latest Test Run for this build (created by PublishTestResults@2)
$runUrl = "$Organization$Project/_apis/test/runs?buildIds=$BuildId&api-version=7.1-preview.3"
$runs = Invoke-RestMethod -Headers $authHeaders -Uri $runUrl -Method GET
if (-not $runs.value -or $runs.count -eq 0) {
  Write-Error "No test runs found for build $BuildId"
  exit 2
}
$run = ($runs.value | Sort-Object completedDate -Descending | Select-Object -First 1)
$runId = $run.id
Write-Host "Using Test Run Id: $runId"

# 3) Get results in the run
$resultsUrl = "$Organization$Project/_apis/test/runs/$runId/results?api-version=7.1-preview.6"
$results = Invoke-RestMethod -Headers $authHeaders -Uri $resultsUrl -Method GET
if (-not $results.value) {
  Write-Error "No test results in run $runId"
  exit 3
}

# 4) For each result, infer the mapping by the storage/name → back to path selector
# JUnit adapters typically populate 'automatedTestStorage' (file) and 'automatedTestName' (test name).
function Build-Selector($r) {
  $file = $r.automatedTestStorage
  $name = $r.automatedTestName
  if ([string]::IsNullOrWhiteSpace($file) -or [string]::IsNullOrWhiteSpace($name)) { return $null }
  # Heuristic for pytest: tests/api/test_orders.py::test_update_order_200
  $fname = $file -replace '\\','/'
  if ($name -match '::') { return "$fname::$name" }
  else { return "$fname::$name" }
}

$patchBody = @()

foreach ($r in $results.value) {
  $sel = Build-Selector $r
  if (-not $sel) { continue }
  # Find the best key in mapping (exact match expected as we constructed selectors similarly)
  if ($pathToCase.ContainsKey($sel)) {
    $caseId = $pathToCase[$sel]
    $patchBody += @{
      id = $r.id
      testCase = @{ id = $caseId }
    }
  }
}

if ($patchBody.Count -eq 0) {
  Write-Warning "No result-to-testCase associations were inferred."
  exit 0
}

# 5) Patch results with testCase linkage
$bodyJson = @{ results = $patchBody } | ConvertTo-Json -Depth 6
$patchUrl = "$Organization$Project/_apis/test/runs/$runId/results?api-version=7.1-preview.6"
Invoke-RestMethod -Headers $authHeaders -Uri $patchUrl -Method Patch -Body $bodyJson

Write-Host "Associated $($patchBody.Count) result(s) to ADO Test Cases."
