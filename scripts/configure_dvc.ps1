param(
    [Parameter(Mandatory = $true)][ValidateSet('gcp', 'aws')][string]$Provider,
    [Parameter(Mandatory = $true)][string]$Bucket,
    [string]$CredentialPath
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '../.venv/Scripts/python.exe'
if (-not (Test-Path '.dvc')) {
    & $python -m dvc init
    if ($LASTEXITCODE -ne 0) { throw 'dvc init failed' }
}
$scheme = if ($Provider -eq 'gcp') { 'gs' } else { 's3' }
& $python -m dvc remote add -f -d labstore "${scheme}://$Bucket/dvc"
if ($LASTEXITCODE -ne 0) { throw 'DVC remote configuration failed' }
if ($Provider -eq 'gcp' -and $CredentialPath) {
    & $python -m dvc remote modify --local labstore credentialpath $CredentialPath
    if ($LASTEXITCODE -ne 0) { throw 'DVC credentials configuration failed' }
}
& $python -m dvc add data/train_batch1.csv data/holdout.csv data/train_batch2.csv
if ($LASTEXITCODE -ne 0) { throw 'dvc add failed' }
& $python -m dvc push
if ($LASTEXITCODE -ne 0) { throw 'DVC push failed; do not git push yet' }
