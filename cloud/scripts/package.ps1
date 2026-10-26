param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[^/]+/mcp$')]
    [string]$McpUrl
)

$ErrorActionPreference = 'Stop'
$cloudRoot = Split-Path -Parent $PSScriptRoot
$packageRoot = Join-Path $cloudRoot 'dist\garmin-cn-sync-cloud'
$zipPath = Join-Path $cloudRoot 'dist\garmin-cn-sync-cloud.zip'
$cloudPrefix = $cloudRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not [IO.Path]::GetFullPath($packageRoot).StartsWith($cloudPrefix, [StringComparison]::OrdinalIgnoreCase) -or
    -not [IO.Path]::GetFullPath($zipPath).StartsWith($cloudPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Package output path resolved outside the cloud directory.'
}

if (Test-Path -LiteralPath $packageRoot) {
    Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null

$escapedUrl = $McpUrl.Replace('\', '\\').Replace('"', '\"')
$mcpText = Get-Content -LiteralPath (Join-Path $cloudRoot 'plugin\.mcp.json.template') -Raw
$mcpText = $mcpText.Replace('__GARMIN_CN_MCP_URL__', $escapedUrl)
$pluginText = Get-Content -LiteralPath (Join-Path $cloudRoot 'plugin\plugin.json.template') -Raw

Set-Content -LiteralPath (Join-Path $packageRoot '.mcp.json') -Value $mcpText -Encoding utf8NoBOM
Set-Content -LiteralPath (Join-Path $packageRoot 'plugin.json') -Value $pluginText -Encoding utf8NoBOM
Copy-Item -LiteralPath (Join-Path $cloudRoot 'README.md') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $cloudRoot 'PRIVACY.md') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $cloudRoot 'TERMS.md') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $cloudRoot 'plugin\SKILL.md') -Destination (Join-Path $packageRoot 'SKILL.md')
Compress-Archive -Path (Join-Path $packageRoot '*') -DestinationPath $zipPath -Force
Write-Output "Package: $zipPath"
