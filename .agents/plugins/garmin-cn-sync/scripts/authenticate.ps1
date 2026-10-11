param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$exitCode = 0

try {
    $pluginRoot = Split-Path -Parent $PSScriptRoot
    $python = Join-Path $pluginRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/setup.ps1 first.' }

    & $python -m garmin_cn_sync.cli auth
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        Write-Host "`n认证失败（退出码 $exitCode）。请保留上方错误信息。" -ForegroundColor Red
    }
    else {
        Write-Host "`n认证成功。" -ForegroundColor Green
    }
}
catch {
    $exitCode = 1
    Write-Host "`n认证脚本失败：$($_.Exception.Message)" -ForegroundColor Red
}

if (-not $NoPause) {
    [void](Read-Host '按 Enter 键关闭窗口')
}

exit $exitCode
