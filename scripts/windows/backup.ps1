# Backup and restore SQLite database

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    uv run python scripts/python/backup_database.py $args
} else {
    python scripts/python/backup_database.py $args
}
