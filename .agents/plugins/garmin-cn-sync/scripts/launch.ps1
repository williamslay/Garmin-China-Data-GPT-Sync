$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $pluginRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Garmin China Sync is not set up. Run scripts/setup.ps1.' }
& $python -m garmin_cn_sync.server
exit $LASTEXITCODE
