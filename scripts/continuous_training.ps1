$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '../.venv/Scripts/python.exe'
& $python append_batch.py
if ($LASTEXITCODE -ne 0) { throw 'Append failed' }
& $python -m dvc add data/train_batch1.csv
if ($LASTEXITCODE -ne 0) { throw 'DVC add failed' }
& $python -m dvc push
if ($LASTEXITCODE -ne 0) { throw 'DVC push failed; Git push must not run' }
git add data/train_batch1.csv.dvc
if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
git commit -m 'data: bo sung 22361 mau du lieu moi (train_batch2)'
if ($LASTEXITCODE -ne 0) { throw 'git commit failed or batch already committed' }
git push origin main
if ($LASTEXITCODE -ne 0) { throw 'git push failed' }
