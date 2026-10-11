$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $pluginRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        & $pyLauncher.Source -3.12 -m venv (Join-Path $pluginRoot '.venv')
    } else {
        $python = Get-Command python -ErrorAction Stop
        & $python.Source -m venv (Join-Path $pluginRoot '.venv')
        if ($LASTEXITCODE -eq 0) {
            & $venvPython -c "import sys; assert sys.version_info >= (3, 12), 'Python 3.12 or newer is required'"
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment: $LASTEXITCODE" }
}
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed: $LASTEXITCODE" }
& $venvPython -m pip install -e "$pluginRoot[dev]"
if ($LASTEXITCODE -ne 0) { throw "Plugin dependency install failed: $LASTEXITCODE" }
Write-Output "Setup complete: $pluginRoot"
