param(
    [string]$TargetDir = "$HOME\.local\bin"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvExe = Join-Path $repoRoot ".venv\Scripts\freedomcoder.exe"

if (-not (Test-Path -LiteralPath $venvExe)) {
    throw "FreedomCoder executable not found at $venvExe. Run `uv sync` first."
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$cmdPath = Join-Path $TargetDir "freedomcoder.cmd"
$cmdText = @"
@echo off
set "FREEDOMCODER_REPO=$repoRoot"
"$venvExe" %*
"@
Set-Content -LiteralPath $cmdPath -Value $cmdText -Encoding ASCII

Write-Output "Installed: $cmdPath"
