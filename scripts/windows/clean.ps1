# Clean temporary files and caches

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    uv run python scripts/python/clean_cache.py $args
} else {
    python scripts/python/clean_cache.py $args
}
