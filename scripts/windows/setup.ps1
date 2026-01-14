# Initialize project: check environment, install dependencies, setup .env, init DB

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    uv run python scripts/python/initialize_project.py $args
} else {
    python scripts/python/initialize_project.py $args
}
