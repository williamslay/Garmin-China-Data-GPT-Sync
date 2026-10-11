$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $pluginRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/setup.ps1 first.' }
& $python -m garmin_cn_sync.cli sync --bootstrap
if ($LASTEXITCODE -ne 0) { throw "Bootstrap sync failed: $LASTEXITCODE" }
