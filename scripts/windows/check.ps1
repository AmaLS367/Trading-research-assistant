# Check project environment and dependencies

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    uv run python scripts/python/check_environment.py $args
} else {
    python scripts/python/check_environment.py $args
}
