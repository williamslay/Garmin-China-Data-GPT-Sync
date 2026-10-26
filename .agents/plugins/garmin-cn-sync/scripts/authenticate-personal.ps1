param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$exitCode = 0
try {
    $pluginRoot = Split-Path -Parent $PSScriptRoot
    $python = Join-Path $pluginRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/setup.ps1 first.' }
    & $python -m garmin_cn_sync.cli auth-personal
    $exitCode = $LASTEXITCODE
}
catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    $exitCode = 1
}
if (-not $NoPause) { [void](Read-Host 'Press Enter to close') }
exit $exitCode
