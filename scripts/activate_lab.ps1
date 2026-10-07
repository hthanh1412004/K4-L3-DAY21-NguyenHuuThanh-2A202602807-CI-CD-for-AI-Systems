# Dot-source from PowerShell: . ./scripts/activate_lab.ps1
$taskEnvFile = Join-Path $PSScriptRoot '../.env'
if (-not (Test-Path -LiteralPath $taskEnvFile)) { throw 'Create .env from .env.example first' }
$taskAllowedVariables = @(
    'MLFLOW_TRACKING_URI', 'MLFLOW_ARTIFACT_ROOT', 'MLFLOW_TRACKING_USERNAME',
    'MLFLOW_TRACKING_PASSWORD', 'CLOUD_PROVIDER', 'AWS_DEFAULT_REGION',
    'AWS_REGION', 'AWS_PROFILE', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
    'AWS_SESSION_TOKEN', 'ARTIFACT_BUCKET', 'MODEL_PATH', 'GOOGLE_APPLICATION_CREDENTIALS'
)
foreach ($taskLine in Get-Content -LiteralPath $taskEnvFile -Encoding utf8) {
    $taskCleanLine = $taskLine.Trim()
    if (-not $taskCleanLine -or $taskCleanLine.StartsWith('#')) { continue }
    $taskPair = $taskCleanLine -split '=', 2
    if ($taskPair.Count -ne 2) { throw 'Invalid .env line' }
    $taskName = $taskPair[0].Trim()
    if ($taskName -notin $taskAllowedVariables) { throw "Unsupported lab variable: $taskName" }
    $taskValue = $taskPair[1].Trim().Trim('"').Trim("'")
    Set-Item -LiteralPath "Env:$taskName" -Value $taskValue
    Write-Output "$taskName configured"
}
